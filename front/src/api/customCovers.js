import axios from "axios";

/*
 * Cover images for the cards of the projects and documents grids: this
 * deployment's own endpoint (app/apps/escr_custom/covers).
 *
 *     { documents: { [pk]: [url, ...] }, projects: { [id]: [url, ...] } }
 */
export const retrieveCovers = async ({ documents = [], projects = [] }) =>
    await axios.get("/custom/covers/", {
        params: {
            documents: documents.join(","),
            projects: projects.join(","),
        },
    });
