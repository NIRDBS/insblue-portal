console.log('fs loaded local');

document.addEventListener('DOMContentLoaded', function () {
    // Notify the parent window when an element is clicked
    document.addEventListener('click', (event) => {
        window.parent.postMessage({
            url: window.location.href
        }, 'https://insblue.incdsb.ro'); // Replace '*' with the parent origin for stricter security
    });
});