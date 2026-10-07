"use client";

import { createContext, useContext } from "react";

/**
 * True inside the presentation mode: the app's screens are shown as slides, without their header
 * and without the links that would leave the presentation (back, compare, open the sheet…).
 */
export const EmbeddedContext = createContext(false);

export const useEmbedded = () => useContext(EmbeddedContext);
