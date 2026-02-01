module.exports = {
    content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
    theme: {
        extend: {
            colors:{
                "variable-collection-color": "var(--variable-collection-color)",
            }
        },
    },
    plugins: [],
}