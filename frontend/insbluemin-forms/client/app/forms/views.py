# Standard library imports
import json
import time
from datetime import datetime
from threading import Lock
from urllib.parse import urljoin

# Third-party imports
import jwt
import requests
from flask import current_app
from hashids import Hashids

# Local application imports
from insbluemin.core.auth_manager import current_user
from insbluemin.core.decorators import *
from insbluemin.core.views import BaseView


class FormioAPI:
    """
    Client for interacting with the Form.io API, handling authentication,
    token caching, and permission enforcement on form requests.
    """

    def __init__(self, api_url, api_key, api_secret, timeout=5):
        """
        Initialize FormioAPI with connection parameters.

        :param api_url: Base URL of the Form.io API
        :param api_key: API key for machine login
        :param api_secret: API secret for machine login
        :param timeout: HTTP request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')  # Ensure no trailing slash
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout

        # Create a single session to reuse TCP connections
        self._session = requests.Session()

        # Token cache variables
        self._token = None
        self._token_expiry = 0
        self._lock = Lock()  # Thread-safety for token refresh

    @staticmethod
    def check_form_permission(user_permissions, form_tags):
        """
        Check if a user has permission to access a form based on tags.

        :param user_permissions: List of permission strings the user has
        :param form_tags: List of tags from the form metadata
        :return: True if form is public or user has required permission, False otherwise
        """
        form_tags = form_tags or []
        # Extract required actions from tags prefixed with 'perm:'
        required_actions = [tag.split(':')[1] for tag in form_tags if tag.startswith('perm:')]

        # Public form if no permissions required
        if not required_actions:
            return True

        # Grant if any user permission ends with required action
        for action in required_actions:
            if any(p.endswith(f".{action}") for p in user_permissions):
                return True

        return False

    def _get_token(self):
        """
        Retrieve and cache a JWT token for Form.io machine authentication.
        Automatically refreshes token if near expiration.

        :return: JWT token string or None on failure
        """
        now = time.time()
        with self._lock:
            # Reuse valid token if expiry is at least 30 seconds away
            if self._token and now + 30 < self._token_expiry:
                return self._token

            payload = {
                "data": {
                    "api_key": self.api_key,
                    "api_secret": self.api_secret
                }
            }
            try:
                # Perform machine login to retrieve JWT header
                resp = self._session.post(
                    urljoin(self.api_url + '/', 'machine/login'),
                    json=payload,
                    timeout=self.timeout
                )
                current_app.logger.debug(resp.json())  # Log full response JSON for debugging
                resp.raise_for_status()
            except requests.RequestException as e:
                current_app.logger.error(f"Formio login failed: {e}")
                return None

            token = resp.headers.get('X-Jwt-Token')
            if not token:
                current_app.logger.error("Token not found in response headers.")
                return None

            try:
                # Decode payload without verifying signature to get expiry
                decoded = jwt.decode(token, options={"verify_signature": False})
                exp = decoded.get('exp')
                if not exp:
                    raise ValueError("No exp in token")
            except Exception as e:
                current_app.logger.error(f"Failed to decode JWT token: {e}")
                return None

            # Cache token and expiry timestamp
            self._token = token
            self._token_expiry = exp
            return token

    def _build_headers(self):
        """
        Construct HTTP headers including authorization token.

        :raises: aborts with 401 if token cannot be retrieved
        :return: dict of headers for API calls
        """
        token = self._get_token()
        if not token:
            abort(401, description="Authentication with Formio failed")
        return {
            'X-Jwt-Token': token
        }

    def _enforce_permissions(self, response, form_id, user_permissions):
        """
        Filter form API responses based on user permissions and handle errors.

        :param response: requests.Response object from API call
        :param form_id: ID or path of the form being accessed
        :param user_permissions: List of current user's permissions
        :return: original or modified response, or Flask error response
        """

        try:
            json_data = response.json()
            # If the response is a list of forms, filter each by permission
            if isinstance(json_data, list):
                filtered = []
                for form in json_data:
                    tags = form.get('tags')
                    if tags:
                        if self.check_form_permission(user_permissions, tags):
                            filtered.append(form)
                            # Update internal content for downstream processing
                        response._content = json.dumps(filtered).encode('utf-8')
                return response

        except ValueError:
            # Non-JSON response
            return jsonify({'message': 'Invalid response from server'}), 500

        # Single form permission check if tags are present
        tags = json_data.get('tags')
        if tags is not None:
            if not self.check_form_permission(user_permissions, tags):
                return jsonify({'message': 'You do not have permission to do that!'}), 403
        else:
            # Fallback: re-fetch tags if not included
            form_url = urljoin(self.api_url + '/', form_id)
            fallback = requests.get(f"{form_url}?select=tags", headers=self._build_headers())
            if fallback.status_code == 200:
                tags = fallback.json().get('tags', [])
                if not self.check_form_permission(user_permissions, tags):
                    return jsonify({'message': 'You do not have permission to do that!'}), 403

        return response

    def _request(self, method, path, form_id=None, json_payload=None, **kwargs):
        """
        Generic HTTP method wrapper: GET, POST, PUT, DELETE.

        Adds auth_user_email to payload for POST calls and enforces permissions.

        :param method: HTTP method name
        :param path: API path or endpoint
        :param form_id: ID/path for permission checks
        :param json_payload: JSON payload for request
        :return: Flask or requests response
        """
        # Build full URL for API call
        url = urljoin(self.api_url + '/', path.lstrip('/'))

        # Attach authenticated user's email for create operations
        if method.upper() == 'POST' and json_payload is not None:
            json_payload.setdefault('data', {})['auth_user_email'] = current_user.email

        headers = self._build_headers()

        try:
            # Execute HTTP request
            resp = self._session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_payload,
                timeout=self.timeout,
                **kwargs
            )
        except requests.RequestException as e:
            current_app.logger.error(f"Formio {method} to {url} failed: {e}")
            abort(502, description="Upstream service error")

        # Check for basic HTTP error codes
        if resp.status_code not in [200, 201, 206]:
            current_app.logger.error(f"Error with request: {resp.text}")
            # abort(403, description=f"{response.text}")
            ## if it returns a 401 here it logs the user out
            payload = json_payload['data']
            payload.pop('auth_user_email')
            error_body = {
                "submit": "error",
                "class": "is-danger",
                "message": f"{resp.text}",
                "data": payload
            }
            status_code = resp.status_code
            if resp.status_code == 401:
                status_code = 403
            return make_response(jsonify(error_body), status_code)

            # abort(resp.status_code, description=f"{resp.text}")

        # Enforce form-level permissions before returning
        return self._enforce_permissions(resp, form_id, current_user.permissions)

    def get(self, path, form_id=None, **kwargs):
        """Perform a GET request on the Form.io API."""
        return self._request('GET', path, form_id, **kwargs)

    def post(self, path, form_id=None, json_payload=None, **kwargs):
        """Perform a POST request on the Form.io API."""
        return self._request('POST', path, form_id, json_payload=json_payload, **kwargs)

    def put(self, path, form_id=None, json_payload=None, **kwargs):
        """Perform a PUT request on the Form.io API."""
        return self._request('PUT', path, form_id, json_payload=json_payload, **kwargs)

    def delete(self, path, form_id=None, **kwargs):
        """Perform a DELETE request on the Form.io API."""
        return self._request('DELETE', path, form_id, **kwargs)


class FormsView(BaseView):
    """
    Flask view for rendering and handling Form.io forms within the application.
    """
    default_view = 'index'

    def __init__(self, app, menu):
        """
        Initialize FormsView and configure Formio client and Hashids.

        :param app: Flask application instance
        :param menu: Application menu registry
        """
        print('Loaded Forms module')  # Indicate module load
        super().__init__(app, menu)

        # Retrieve configuration values
        self.formio = FormioAPI(
            api_url=app.config.get('FORMIO_API_URL'),
            api_key=app.config.get('FORMIO_API_KEY'),
            api_secret=app.config.get('FORMIO_API_SECRET')
        )
        # Initialize Hashids for obfuscating submission IDs
        self.hashids = Hashids(
            salt=app.config.get('HASHIDS_SALT', 'default_salt'),
            min_length=24,
            alphabet=app.config.get('HASHIDS_ALPHABET', 'abcdefghijklmnopqrstuvwxyz1234567890')
        )

    def encode_submission_id(self, object_id: str) -> str:
        """
        Obfuscate a MongoDB ObjectId string using Hashids.

        :param object_id: 24-character hex string of the ObjectId
        :return: Obfuscated hashid string
        :raises ValueError: If object_id is not valid length or type
        """
        if not isinstance(object_id, str) or len(object_id) != 24:
            raise ValueError("Invalid ObjectId format")
        return self.hashids.encode_hex(object_id)

    def decode_submission_id(self, obfuscated_id: str) -> str:
        """
        Decode an obfuscated submission ID back to the original ObjectId.

        :param obfuscated_id: Hashids-generated string
        :return: Original 24-character ObjectId string
        :raises ValueError: If decoding fails or result is invalid
        """
        try:
            object_id = self.hashids.decode_hex(obfuscated_id)
            if not object_id or len(object_id) != 24:
                raise ValueError()
            return object_id
        except Exception as e:
            raise ValueError(f"Invalid or corrupt submission ID: {obfuscated_id}") from e

    @add_to_menu(location='sidebar', group='Forms', parent='Forms:fa-solid fa-file-lines', label='Formulare', icon='fa-solid fa-file')  # noqa: E501
    @has_permissions(['forms.can_read', 'forms.can_read_all'])
    @expose('/', methods=['GET'])
    def index(self):
        """
        Render a list of available forms, optionally filtered by category.

        Query Parameters:
          - category: Filter forms by category tag (case-insensitive)
          - form=json: Return JSON response instead of HTML

        :return: JSON or rendered template with form list
        """
        response = self.formio.get("form?type=form&select=title,name,path,tags,components")

        forms = []
        requested_category = request.args.get('category', '').lower()
        for form in response.json():
            tags = form.get("tags", [])
            if not tags:
                continue  # Skip forms without tags

            # Extract category tags prefixed with 'cat:'
            categories = [tag.split("cat:")[1] for tag in tags if tag.startswith("cat:")]
            if requested_category and requested_category not in [c.lower() for c in categories]:
                continue

            # Use first component's 'content' as description
            description = form.get('components', [{}])[0].get('content', '')
            form.update({
                "category": categories,
                "description": description,
                "path": self.app.config.get('APPLICATION_ROOT') + 'view/' + form.get('path')
            })
            form.pop("tags", None)
            form.pop("components", None)
            forms.append(form)
            print(self.app.config.get('APPLICATION_ROOT'))
        if request.args.get('form') == 'json':
            return jsonify(forms)
        return self.render_template('forms.jinja2', title='Forms', forms=forms)

    @has_permissions(['forms.can_read', 'forms.can_read_all'])
    @expose('/view/<form_path>', methods=['GET'])
    def form_view(self, form_path):
        """
        Display a single form for user submission.

        :param form_path: Path identifier for the form
        :return: JSON or rendered form template
        """
        if form_path == 'favicon.ico':
            return '', 204  # Ignore favicon requests

        response = self.formio.get(f"{form_path}?select=title,tags,name,components", form_id=form_path)
        form_data = response.json()
        # Remove internal auth_user_email field from form components
        form_json = {
            'components': [c for c in form_data.get('components', []) if c.get('key') != 'auth_user_email']
        }

        if request.args.get('form') == 'json':
            form_data['path'] = request.path
            return jsonify(form_data)
        return self.render_template('forms-form.jinja2', title=form_data.get('title'), form_json=form_json)

    @has_permissions(['forms.can_create'])
    @expose('/view/<form_path>', methods=['POST'])
    def form_post(self, form_path):
        """
        @todo: Probably a good idea to encode all _ids
        Handle submission of a form by POSTing data to Form.io.

        :param form_path: Path identifier for the form
        :return: JSON payload of created submission data
        """
        payload = request.get_json()
        response = self.formio.post(f"{form_path}/submission", form_id=form_path, json_payload=payload)
        if response.status_code in [200, 201]:
            # Return only the 'data' section of the response
            return jsonify(response.json().get('data'))

        return response

    @has_permissions(['forms.can_read', 'form.can_read_all'])
    @expose('/view/<form_path>/submission', methods=['GET'])
    def form_submissions(self, form_path):
        """
        List submissions for the current user on a form.

        :param form_path: Path identifier for the form
        :return: JSON or rendered template with submissions list
        """
        # Filter to only submissions by this user
        submission_resp = self.formio.get(
            f"{form_path}/submission?data.auth_user_email={current_user.email}",
            form_id=form_path
        )
        submissions = submission_resp.json()
        for sub in submissions:
            # Obfuscate the internal MongoDB _id
            sub['obfuscated_id'] = self.encode_submission_id(sub.pop('_id'))
            # Convert ISO timestamp to datetime object
            sub['created'] = datetime.fromisoformat(sub['created'].replace('Z', '+00:00'))

        if request.args.get('form') == 'json':
            return jsonify(submissions)
        return self.render_template('forms-submissions.jinja2', title=form_path, submissions=submissions)

    @has_permissions(['forms.can_read', 'form.can_read_all'])
    @expose('/view/<form_path>/submission/<submission_id>', methods=['GET'])
    def form_single_submission(self, form_path, submission_id):
        """
        View details of a single submission by its obfuscated ID.

        :param form_path: Path identifier for the form
        :param submission_id: Obfuscated submission ID
        :return: JSON or rendered submission detail template
        """
        # Decode obfuscated ID back to MongoDB ObjectId
        real_id = self.decode_submission_id(submission_id)
        response = self.formio.get(f"{form_path}/submission/{real_id}", form_id=form_path)

        if request.args.get('form') == 'json':
            return jsonify(response.json())
        return self.render_template('forms-submission-view.jinja2', title=form_path)

    @has_permissions(['forms.can_update', 'form.can_update_all'])
    @expose('/view/<form_path>/submission/<submission_id>', methods=['PUT'])
    def form_put(self, form_path, submission_id):
        """
        Update an existing submission with new data.

        :param form_path: Path identifier for the form
        :param submission_id: Obfuscated submission ID
        :return: JSON payload of updated submission
        """
        real_id = self.decode_submission_id(submission_id)
        payload = request.get_json()
        response = self.formio.put(
            f"{form_path}/submission/{real_id}",
            form_id=form_path,
            json_payload=payload
        )

        return jsonify(response.json())
