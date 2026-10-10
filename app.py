import datetime as dt
import os

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import utils as U

MIN_COMMON_ML = 5

st.set_page_config(page_title="Recomendador de películas", page_icon="🎬", layout="wide")

# ----------------------------------------------------------------------- course form (secrets)
def secret(key):
    try:
        return st.secrets.get(key, None)
    except Exception:                               # no secrets file
        return None


UNLOCK_CODE = secret("unlock_code")
COURSE_SHEET = secret("sheet_url")


# ----------------------------------------------------------------------- cached loaders
@st.cache_data
def load_movie_map():
    return pd.read_csv(f"{U.DATA}/movie_map.csv")


@st.cache_data(ttl=300, show_spinner="Descargando respuestas del formulario...")
def load_form(link):
    return U.read_sheet(link)


@st.cache_data
def load_ml():
    ml, titles, wide = U.load_movielens()
    cands = U.candidate_ids(ml, 50)
    counts = ml["movieId"].value_counts()
    return ml, titles, wide, list(cands), counts


# ----------------------------------------------------------------------- sidebar
FORMAT_HELP = """
La hoja de respuestas (la que genera Google Forms) debe tener:

1. **Primera columna:** marca temporal (*Timestamp*), como la crea Google Forms.
2. **Columnas intermedias:** una por película, en una pregunta de tipo *cuadrícula de selección múltiple*
   (o similar), con el título entre corchetes al final del encabezado, por ejemplo
   `¿Te gustó...? [El Padrino]`.
3. **Última columna:** nombre del estudiante (debe ser único; si se repite, se usa la última respuesta).

**Respuestas aceptadas** (las celdas vacías significan «no la vi»):

| Respuesta | Calificación |
|---|---|
| Me gustó totalmente / **5** | 5 |
| Me gustó / **4** | 4 |
| Ni me gustó, ni disgustó / **3** | 3 |
| No me gustó / **2** | 2 |
| No me gustó para nada / **1** | 1 |

Las columnas sin calificaciones reconocidas se ignoran y se avisa cuál. La hoja debe estar compartida
como «Cualquier persona con el enlace puede ver».

Para recomendar con MovieLens, las películas que no estén en el mapeo del curso necesitan su `movieId`
(se sube en la pestaña MovieLens).
"""

movie_map = load_movie_map()

st.sidebar.header("Datos del formulario")
own_link = st.sidebar.text_input(
    "Enlace a la hoja de respuestas (Google Sheets)", placeholder="https://docs.google.com/spreadsheets/d/...",
    help="Es la hoja con las respuestas de tu formulario, no el enlace forms.gle. "
         "Debe estar compartida como «Cualquier persona con el enlace puede ver».")
code = ""
if UNLOCK_CODE and COURSE_SHEET:
    code = st.sidebar.text_input("Código del curso (opcional)", type="password",
                                 help="Carga el formulario del curso en vez de uno propio.")
use_course = bool(code) and code == UNLOCK_CODE
if code and not use_course:
    st.sidebar.error("Código incorrecto.")
link = own_link.strip() or (COURSE_SHEET if use_course else "")
with st.sidebar.expander("ℹ️ Estructura requerida del formulario"):
    st.markdown(FORMAT_HELP)
GUIDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "guia_profesores.pdf")
if os.path.exists(GUIDE):
    with open(GUIDE, "rb") as f:
        st.sidebar.download_button("📄 Descargar guía para profesores (PDF)", f.read(),
                                   "guia_profesores.pdf", "application/pdf", key="dl_guide")
if not link:
    st.title("🎬 Recomendador de películas")
    st.info("Pega en la barra lateral el enlace a la hoja de Google Sheets con las respuestas de tu formulario, "
            "o ingresa el código del curso.")
    st.stop()
if st.sidebar.button("Recargar datos"):
    st.cache_data.clear()

try:
    raw = load_form(link)
    form, builtin_ids, originals, notes = U.parse_form(raw, movie_map)
except U.SheetError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    st.error(f"No se pudo leer la hoja: {e}")
    st.stop()

if notes:
    st.sidebar.warning("Avisos al leer la hoja:\n\n" + "\n".join(f"- {t}" for t in notes))
N_FORM_MOVIES = len(builtin_ids)
if form.empty:
    st.error("La hoja no tiene respuestas válidas.")
    st.stop()

min_date = form["timestamp"].min().date()
max_date = form["timestamp"].max().date()
start = st.sidebar.date_input("Desde (fecha)", value=min_date, min_value=min_date, max_value=max_date,
                              key=f"from_{hash(link)}",
                              help="Se conservan las respuestas desde esta fecha y hora (ver «Desde (hora)»).")
start_time = st.sidebar.time_input("Desde (hora)", value=dt.time(0, 0), step=300, key=f"time_{hash(link)}",
                                   help="Se aplica a la fecha «Desde»: útil para separar secciones del mismo día.")
start_dt = dt.datetime.combine(start, start_time)
MIN_RATINGS = int(st.sidebar.number_input("Mínimo de películas calificadas", 1, N_FORM_MOVIES,
                                          min(4, N_FORM_MOVIES)))

ratings, kept_ts = U.build_ratings(form, start_dt, MIN_RATINGS)
if len(ratings) < 3:
    st.error("Con estos filtros quedan menos de 3 estudiantes. Cambia la fecha o el mínimo de calificaciones.")
    st.stop()

MOVIES = list(ratings.columns)
R = ratings.to_numpy(dtype=float)
users = list(ratings.index)
D, common = U.distances(R)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**{len(users)}** estudiantes · **{len(MOVIES)}** películas · "
    f"**{np.mean(~np.isnan(R)):.0%}** de celdas calificadas  \n"
    f"Respuestas del {kept_ts.min():%d-%m-%Y} al {kept_ts.max():%d-%m-%Y}")

st.sidebar.download_button(
    "⬇️ Descargar calificaciones (Excel)",
    U.ratings_to_excel(ratings, U.english_titles(MOVIES, movie_map)),
    f"calificaciones_desde_{start_dt:%Y-%m-%d_%H%M}.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_ratings",
    help="Una fila por estudiante y una columna por película (1 a 5, vacío = no la vio), con la fecha "
         "y hora «Desde» y el mínimo de películas calificadas aplicados. Incluye los nombres.")

movie_table = pd.DataFrame({"Película": MOVIES,
                            "Calificaciones": ratings.notna().sum().to_numpy(),
                            "Promedio": ratings.mean().round(2).to_numpy()})
with st.sidebar.expander(f"Películas del formulario ({len(MOVIES)})"):
    st.dataframe(movie_table, hide_index=True, use_container_width=True)
    st.download_button("Descargar nombres (CSV)", U.mapping_template(MOVIES, builtin_ids, originals),
                       "peliculas_formulario.csv", "text/csv", key="dl_sidebar",
                       help="Completa la columna movieId y súbela en la pestaña MovieLens.")

# ----------------------------------------------------------------------- tabs
st.title("🎬 Recomendador de películas")
tab1, tab2 = st.tabs(["Compañeros", "MovieLens"])

selected = None          # name of the student chosen in tab 1 (used by tab 2)

with tab1:
    st.caption("Recomendaciones basadas en usuarios: k vecinos más cercanos (`KNNImputer` de scikit-learn).")

    c1, c2 = st.columns(2)
    query = c1.text_input("Buscar estudiante")
    matches = [u for u in users if query.strip().lower() in u.lower()]
    if not matches:
        c2.info("Ningún estudiante coincide con la búsqueda.")
    else:
        selected = c2.selectbox("Estudiante", matches)

    if selected is not None:
        i = users.index(selected)

        # ---- similar classmates
        st.subheader("Compañeros más parecidos")
        min_common = st.slider("Mínimo de películas en común", 0, len(MOVIES), min(5, len(MOVIES)),
                               help="Quien comparte pocas películas puede parecer idéntico por casualidad.")
        near = pd.DataFrame({"Estudiante": users, "Distancia": D[i], "Películas en común": common[i]})
        near = near.drop(index=i)
        near = near[near["Películas en común"] >= min_common].sort_values("Distancia", kind="stable")
        top = near.head(10).reset_index(drop=True)
        top.insert(0, "Rank", top.index + 1)
        top["Distancia"] = top["Distancia"].round(2)
        if top.empty:
            st.info("Nadie cumple el mínimo de películas en común.")
        else:
            st.dataframe(top, hide_index=True, use_container_width=True)
            st.caption("Distancia euclidiana calculada solo con las películas que ambos calificaron "
                       "(reescalada por las que faltan): **menor = más parecido**.")
            side_users = [selected] + [users[users.index(n)] for n in top["Estudiante"].head(3)]
            st.dataframe(ratings.loc[side_users].T, use_container_width=True,
                         column_config={u: st.column_config.NumberColumn(format="%d") for u in side_users})

        # ---- predictions
        st.subheader("Películas que no ha visto: predicciones")
        k = st.slider("k (número de vecinos)", 1, 30, 4)
        unseen = [c for c in range(len(MOVIES)) if np.isnan(R[i, c])]
        if not unseen:
            st.success(f"{selected} ha visto las {len(MOVIES)} películas: no hay nada que predecir.")
        else:
            filled = U.predict_all(R, k)
            rows = []
            for c in unseen:
                nb = U.neighbors_behind(R, D, i, c, k)
                rows.append({"Película": MOVIES[c],
                             "Predicción": round(float(filled[i, c]), 2),
                             f"Los {k} compañeros detrás de la predicción":
                                 "; ".join(f"{U.short_name(users[j])} ({R[j, c]:.0f})" for j in nb)})
            pred = pd.DataFrame(rows).sort_values("Predicción", ascending=False)
            st.dataframe(pred, hide_index=True, use_container_width=True)

            movie = st.selectbox("Detalle de una predicción", pred["Película"].tolist())
            c = MOVIES.index(movie)
            nb = U.neighbors_behind(R, D, i, c, k)
            detail = pd.DataFrame({"Vecino": [users[j] for j in nb],
                                   "Distancia": [round(float(D[i, j]), 2) for j in nb],
                                   "Su calificación": [int(R[j, c]) for j in nb]})
            with st.container(border=True):
                st.dataframe(detail, hide_index=True, use_container_width=True)
                st.markdown(f"Promedio de {len(nb)} vecinos: **{detail['Su calificación'].mean():.2f}**")

    with st.expander("Mapa de calor de la matriz de calificaciones"):
        if selected is not None:                    # selected student first, then by distance to them
            d = np.where(np.isnan(D[users.index(selected)]), np.inf, D[users.index(selected)])
            d[users.index(selected)] = -1
            order = ratings.index[np.argsort(d, kind="stable")]
        else:
            order = ratings.notna().sum(axis=1).sort_values(ascending=False, kind="stable").index
        long = (ratings.loc[order].reset_index(names="Estudiante")
                .melt(id_vars="Estudiante", var_name="Película", value_name="Calificación")
                .dropna())
        heat = alt.Chart(long).mark_rect().encode(
            x=alt.X("Película:N", sort=MOVIES),
            y=alt.Y("Estudiante:N", sort=list(order), axis=alt.Axis(labels=False, ticks=False)),
            color=alt.Color("Calificación:Q", scale=alt.Scale(scheme="redyellowgreen", domain=[1, 5])),
            tooltip=["Estudiante", "Película", "Calificación"]).properties(height=500)
        st.altair_chart(heat, use_container_width=True)
        st.caption("Blanco = película no vista. "
                   + (f"Primera fila: {selected}; debajo, sus compañeros del más al menos parecido (menor distancia primero)."
                      if selected is not None else "Ordenado por número de películas calificadas."))

with tab2:
    ml, titles, wide, cands, counts = load_ml()
    st.caption("MovieLens: usuarios mayormente de EE.UU. que calificaron películas entre 1996 y 2018 "
               "(escala de media estrella). Sus gustos pueden diferir de los de tu curso.")

    # ---- movie -> MovieLens id mapping (built-in for the course form, upload for other forms)
    ids, id_problems = U.resolve_ids(MOVIES, builtin_ids, None, set(wide.columns), originals)
    with st.expander("Mapeo de las películas del formulario a MovieLens", expanded=not ids.notna().any()):
        st.markdown("Para recomendar con MovieLens, cada película necesita su `movieId`. Descarga la lista, "
                    "completa la columna `movieId` (búscalo en `movies.csv` de MovieLens) y súbela aquí. "
                    "El archivo se usa solo en esta sesión y no se guarda.")
        st.download_button("Descargar nombres (CSV)", U.mapping_template(MOVIES, builtin_ids, originals),
                           "peliculas_formulario.csv", "text/csv", key="dl_tab2")
        up = st.file_uploader("Subir mapeo (CSV con columnas title y movieId)", type=["csv", "txt"])
        upload = None
        if up is not None:
            try:
                upload, bad_rows = U.read_mapping(up.getvalue())
                ids, more = U.resolve_ids(MOVIES, builtin_ids, upload, set(wide.columns), originals)
                id_problems = bad_rows + more
            except U.SheetError as e:
                st.error(str(e))
        mapped = list(ids.dropna().index)
        st.markdown(f"**{len(mapped)} de {len(MOVIES)}** películas con `movieId` válido.")
        if id_problems:
            st.warning("\n".join(f"- {p}" for p in id_problems))
    mapped_idx = [MOVIES.index(t) for t in mapped]
    form_ids = [int(ids[t]) for t in mapped]
    min_common_ml = min(MIN_COMMON_ML, max(len(mapped), 1))

    c1, c2 = st.columns(2)
    k_ml = c1.slider("k (número de vecinos)", 1, 50, 20, key="k_ml")
    n_rec = int(c2.number_input("Número de recomendaciones", 1, 50, 10))

    if selected is None:
        st.info("Elige un estudiante en la pestaña «Compañeros».")
    elif not mapped:
        st.info("Sube el mapeo de películas a MovieLens para obtener recomendaciones.")
    elif np.isnan(R[users.index(selected), mapped_idx]).all():
        st.info(f"{selected} no calificó ninguna de las películas con `movieId`: no hay base para recomendar.")
    else:
        i = users.index(selected)
        st.markdown(f"Recomendaciones para **{selected}**")
        preds, near_ml = U.recommend_for_student(wide, form_ids, cands, R[i, mapped_idx], k_ml, min_common_ml)
        if preds is None:
            st.warning(f"Ningún usuario de MovieLens calificó al menos {min_common_ml} de las películas "
                       "con `movieId`. Agrega más películas al mapeo.")
        else:
            top = preds.sort_values(ascending=False).head(n_rec)
            st.dataframe(pd.DataFrame({"Película": [titles[m] for m in top.index],
                                       "Predicción": top.round(2).to_numpy(),
                                       "Calificaciones en MovieLens": [int(counts[m]) for m in top.index]}),
                         hide_index=True, use_container_width=True)
            st.caption(f"Vecinos: {len(near_ml)} usuarios de MovieLens que calificaron al menos {min_common_ml} "
                       f"de las {len(mapped)} películas con `movieId`. "
                       "Candidatas: películas con al menos 50 calificaciones, sin las del formulario.")
            if len(near_ml) < 30:
                st.warning("Hay pocos vecinos en MovieLens: las predicciones serán poco confiables.")

            st.subheader("Usuarios de MovieLens más parecidos")
            show = near_ml.head(10).copy()
            show.insert(0, "Rank", show.index + 1)
            show["distance"] = show["distance"].round(2)
            st.dataframe(show.rename(columns={"userId": "Usuario (userId)", "distance": "Distancia",
                                              "common": "Películas en común"}),
                         hide_index=True, use_container_width=True)
            st.caption("Distancia calculada con las películas del formulario que ambos calificaron "
                       "(menor = más parecido). Cada predicción usa los k usuarios más cercanos que calificaron "
                       "esa película, por lo que no son exactamente estos.")

    st.markdown("---")
    st.caption("F. Maxwell Harper and Joseph A. Konstan (2015). *The MovieLens Datasets: History and Context.* "
               "ACM Transactions on Interactive Intelligent Systems 5(4): 19:1–19:19. "
               "https://doi.org/10.1145/2827872 · Uso educativo y de investigación; sin respaldo de GroupLens.")
