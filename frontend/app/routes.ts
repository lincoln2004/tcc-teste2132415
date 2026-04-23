import { type RouteConfig, index, route, layout, prefix } from "@react-router/dev/routes";

export default [
  layout("routes/layout.tsx", [
    index("routes/homepage.tsx"),
    route("upload", "routes/upload_archives.tsx"),
    ...prefix("decisions", [
      index("routes/filtercolumns.tsx"),
      route("models", "routes/modelspage.tsx"),
    ]),
    route("report", "routes/reportpage.tsx"),
  ]),
] satisfies RouteConfig;
