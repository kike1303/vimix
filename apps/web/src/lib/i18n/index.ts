import { browser } from "$app/environment";
import { init, register, getLocaleFromNavigator } from "svelte-i18n";

register("en", () => import("./en.json"));
register("es", () => import("./es.json"));

init({
  fallbackLocale: "en",
  initialLocale: browser ? getLocaleFromNavigator()?.split("-")[0] : "en",
});
