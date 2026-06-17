import { createRouter, createWebHistory } from "vue-router";
import RunList from "../views/RunList.vue";
import RunDetail from "../views/RunDetail.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "runs", component: RunList },
    { path: "/runs/:runId", name: "run-detail", component: RunDetail, props: true },
  ],
});
