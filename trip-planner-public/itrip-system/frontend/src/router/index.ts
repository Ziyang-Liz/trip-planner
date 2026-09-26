import { createRouter, createWebHistory } from "vue-router";
import Homepage from "../pages/Homepage.vue";
import PlannerResult from "../pages/PlannerResult.vue";

const routes = [
  {
    path: "/",
    name: "home",
    component: Homepage,
  },
  {
    path: "/planner",
    name: "planner",
    component: PlannerResult,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;