/**
 * 
 * @param {any} o 
 * @returns {boolean}
 */
function isObj(o) {
    return typeof o === 'object' && !Array.isArray(o) && o !== null
}
/**
 * @param {string} id
 * @returns {Element}
 **/
function $(id) { return document.getElementById(id); }

/**
 * @param {string} className
 * @returns {Element}
 **/
function _(className) { return document.getElementsByClassName(className)[0]; }

/**
 * 
 * @param {string} className 
 * @returns {HTMLCollectionOf<Element>}
 */
function _a(className) { return document.getElementsByClassName(className); }

function getSelectedSection() {
    return document.querySelector("#side-panel>button.selected");
}
function updateSectionSelectionDiv() {
    let div = $("section-selector");
    let sel = getSelectedSection();
    let r = sel.getBoundingClientRect();
    div.style.height = `${r.height}px`;
    div.style.width = `${r.width}px`;
    div.style.top = `${sel.offsetTop}px`;
    div.style.left = `${sel.offsetLeft}px`;
    if (div.checkVisibility()) {
        setTimeout(() => {
            div.style.visibility = "visible";
        }, 500);
    }
}
function deselectSection() {
    getSelectedSection().classList.remove("selected");
}

document.addEventListener('DOMContentLoaded', () => {
    Array.from(_a("section-button")).forEach(element => {
        element.addEventListener('click', (e) => {
            deselectSection();
            e.currentTarget.classList.add("selected");
            updateSectionSelectionDiv();
        });
    });
    updateSectionSelectionDiv();
    // params = new URLSearchParams(window.location.search);
    // if (params.has('projectid')) {
    //     loadProject(params.get('projectid'));
    // }
});