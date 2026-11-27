/*
 * Instance and user settings the base template writes on the standalone
 * navigation's mount point (#vue-global-nav) on every page. Read once when the
 * bundle loads (the standalone app replaces that element later), so Vue pages
 * get them without their Django templates having to pass them in.
 */
const mountPoint = document.querySelector("#vue-global-nav > global-navigation");

const flag = (name) => mountPoint?.getAttribute(`:${name}`) === "true";

export default {
    isAuthenticated: flag("is-authenticated"),
    searchDisabled: flag("search-disabled"),
};
