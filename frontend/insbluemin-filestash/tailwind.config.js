/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./flask/**/templates/**/*.jinja2",
        "./flask/**/static/**/*.js",
        "./node_modules/flowbite/**/*.js",
        "/Volumes/HD/Work/INCDSB/_devops/docker-insblue-framework/insblue-flask/insbluemin-core/insbluemin/core/templates/**/*.jinja2"
    ],
    safelist: [{
        pattern: /grid-cols-*/, // You can display all the colors that you need
        variants: ['sm', 'md', 'lg'], // Optional
    },
        {
            pattern: /^[\w:]*col-span-/, // You can display all the colors that you need
            variants: ['sm', 'md', 'lg'], // Optional
        }, 'pattern2'
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: {
                    "50": "#eff6ff",
                    "100": "#dbeafe",
                    "200": "#bfdbfe",
                    "300": "#93c5fd",
                    "400": "#60a5fa",
                    "500": "#3b82f6",
                    "600": "#2563eb",
                    "700": "#1d4ed8",
                    "800": "#1e40af",
                    "900": "#1e3a8a",
                    "950": "#172554"
                },
                insblue: {
                    lighter: '#009BFF',
                    light: '#0093FD',
                    med: '#0870BF',
                    dark: '#11447E',
                    darker: '#172650',
                },
                insgrey: {
                    lighter: '#F9F9F9',
                    light: '#F7F7F7',
                }
            }
        },
        fontFamily: {
            'body': [
                'Inter',
                'ui-sans-serif',
                'system-ui',
                '-apple-system',
                'system-ui',
                'Segoe UI',
                'Roboto',
                'Helvetica Neue',
                'Arial',
                'Noto Sans',
                'sans-serif',
                'Apple Color Emoji',
                'Segoe UI Emoji',
                'Segoe UI Symbol',
                'Noto Color Emoji'
            ],
            'sans': [
                'Inter',
                'ui-sans-serif',
                'system-ui',
                '-apple-system',
                'system-ui',
                'Segoe UI',
                'Roboto',
                'Helvetica Neue',
                'Arial',
                'Noto Sans',
                'sans-serif',
                'Apple Color Emoji',
                'Segoe UI Emoji',
                'Segoe UI Symbol',
                'Noto Color Emoji'
            ],
            'sans-narrow': ['PT Sans Narrow'],
            'sans-normal': ['PT Sans'],
            'sans-caption': ['PT Sans Caption'],
            'roboto': ['Roboto'],
        }
    },
    plugins: [
        require("flowbite/plugin"),
        require('@tailwindcss/typography'),
    ]
}
