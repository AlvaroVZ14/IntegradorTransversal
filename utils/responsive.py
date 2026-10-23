"""Comunica solo el breakpoint de pantalla; sin librerías nuevas."""
import streamlit as st
from streamlit.components.v2 import component

def _crear_viewport():
    return component(
        "mente_futuro_dashboard_viewport",
        html="<span aria-hidden='true'></span>",
        js="""
        export default function({data, setStateValue}) {
          const media = window.matchMedia('(max-width: 767px)');
          const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
          let last = data.mobile;
          let lastMotion = data.reduced;
          const report = () => {
            if (media.matches !== last) {
              last = media.matches;
              setStateValue('mobile', last);
            }
            if (motion.matches !== lastMotion) {
              lastMotion = motion.matches;
              setStateValue('reduced', lastMotion);
            }
          };
          report();
          media.addEventListener('change', report);
          motion.addEventListener('change', report);
          return () => {media.removeEventListener('change', report);motion.removeEventListener('change', report);};
        }
        """,
    )


def es_pantalla_movil():
    default = st.session_state.get("dashboard_mobile", False)
    reduced = st.session_state.get("dashboard_reduced_motion", True)
    result = _crear_viewport()(data={"mobile": default,"reduced":reduced}, default={"mobile": default,"reduced":reduced},
              on_mobile_change=lambda: None, on_reduced_change=lambda: None, key="dashboard_viewport", height=0)
    mobile = bool(result.mobile)
    st.session_state["dashboard_mobile"] = mobile
    st.session_state["dashboard_reduced_motion"] = bool(result.reduced)
    return mobile
