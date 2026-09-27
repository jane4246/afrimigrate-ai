function escapeHtml(value) {

    return String(value).replace(
        /[&<>"']/g,

        function (character) {

            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            }[character];

        }
    );

}