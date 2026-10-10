"""Builds docs/guia_profesores.pdf (instructions for professors). Needs: pip install reportlab.

Run from the project folder:  python docs/make_guide.py
"""
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guia_profesores.pdf")

ACCENT = colors.HexColor("#1f4e79")
LIGHT = colors.HexColor("#eaf1f8")

ss = getSampleStyleSheet()
body = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica", fontSize=10, leading=14, alignment=TA_LEFT,
                      spaceAfter=6)
small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"))
cell = ParagraphStyle("cell", parent=body, fontSize=9, leading=12, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold", textColor=colors.white)
h1 = ParagraphStyle("h1", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26,
                    textColor=ACCENT, alignment=TA_LEFT, spaceAfter=4)
sub = ParagraphStyle("sub", parent=body, fontSize=11, textColor=colors.HexColor("#555555"), spaceAfter=14)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18,
                    textColor=ACCENT, spaceBefore=14, spaceAfter=6, keepWithNext=1)
h3 = ParagraphStyle("h3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=11, leading=14,
                    spaceBefore=8, spaceAfter=3, keepWithNext=1)
code = ParagraphStyle("code", parent=body, fontName="Courier", fontSize=9, leading=12)


def P(t, st=body):
    return Paragraph(t, st)


def bullets(items, numbered=False):
    return ListFlowable([ListItem(P(t), leftIndent=14) for t in items],
                        bulletType="1" if numbered else "bullet", start="1" if numbered else "•",
                        leftIndent=14, bulletFontSize=9)


def table(rows, widths, header=True):
    data = [[P(c, cellb if (header and r == 0) else cell) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4d0")),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), ACCENT))
        st += [("BACKGROUND", (0, r), (-1, r), LIGHT) for r in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st))
    return t


def note(text):
    t = Table([[P(text, cell)]], colWidths=[17 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawString(2 * cm, 1.2 * cm, "Recomendador de películas - Guía para profesores")
    canvas.drawRightString(letter[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


s = []
s += [P("Recomendador de películas", h1),
      P("Guía para profesores: cómo usar la aplicación con el formulario de su curso", sub)]

s += [P("1. ¿Qué hace la aplicación?", h2),
      P("La aplicación lee las calificaciones de películas que sus estudiantes respondieron en un formulario de "
        "Google y muestra, con un método de <b>filtrado colaborativo</b> (k vecinos más cercanos):"),
      bullets(["qué compañeros tienen gustos más parecidos a los de cada estudiante;",
               "qué calificación se predice para las películas que el estudiante no ha visto, y en qué compañeros "
               "se basa cada predicción;",
               "qué películas de un catálogo mucho más grande (<b>MovieLens</b>) se le recomendarían, y qué usuarios "
               "de MovieLens se parecen más a él o ella."]),
      P("La aplicación no guarda las respuestas en archivos: lee la hoja de Google en vivo cada vez que se carga "
        "o se pulsa «Recargar datos».")]

s += [P("2. Paso 1: preparar el formulario", h2),
      P("La aplicación espera la hoja de respuestas que genera Google Forms con esta estructura:"),
      table([["Columna", "Contenido"],
             ["Primera", "Marca temporal (<i>Timestamp</i>), que Google Forms agrega automáticamente."],
             ["Intermedias", "Una columna por película. Se obtienen con una pregunta de tipo <b>cuadrícula de "
                             "selección múltiple</b>: las películas son las filas y las opciones de respuesta son "
                             "las columnas. Google escribe el encabezado como "
                             "<font name='Courier'>Pregunta... [Nombre de la película]</font>; la aplicación toma "
                             "como título lo que está entre corchetes."],
             ["Última", "Nombre del estudiante (pregunta de texto corto, <b>al final</b> del formulario)."]],
            [3 * cm, 14 * cm]),
      Spacer(1, 6),
      P("<b>Respuestas aceptadas.</b> Cada celda se convierte en una calificación de 1 a 5. Una celda vacía "
        "significa «no la vi»."),
      table([["Respuesta en el formulario", "Calificación"],
             ["Me gustó totalmente  (o el número 5)", "5"],
             ["Me gustó  (o 4)", "4"],
             ["Ni me gustó, ni disgustó  (o 3)", "3"],
             ["No me gustó  (o 2)", "2"],
             ["No me gustó para nada  (o 1)", "1"]],
            [11 * cm, 6 * cm]),
      Spacer(1, 6),
      note("<b>Consejos.</b> Use las cinco opciones en la cuadrícula con exactamente estos textos, o bien una escala "
           "numérica de 1 a 5. Si el texto es distinto (otro idioma u otras palabras) esas respuestas no se "
           "reconocen y la columna se ignora. Pida el nombre completo: si un nombre se repite, la aplicación usa "
           "la última respuesta de esa persona. Idealmente use entre 15 y 30 películas conocidas; con muy pocas "
           "películas las recomendaciones son poco confiables.")]

s += [P("3. Paso 2: compartir la hoja de respuestas", h2),
      bullets(["En Google Forms, abra la pestaña <b>Respuestas</b> y pulse <b>Vincular con Hojas de cálculo</b> "
               "(o abra la hoja ya vinculada).",
               "En la hoja, pulse <b>Compartir</b> y en «Acceso general» elija "
               "<b>Cualquier persona con el enlace</b> con rol <b>Lector</b>.",
               "Copie el enlace de la barra del navegador. Debe ser el de la <b>hoja</b> "
               "(<font name='Courier'>docs.google.com/spreadsheets/d/...</font>), no el enlace del formulario "
               "(<font name='Courier'>forms.gle/...</font>).",
               "Si la hoja tiene varias pestañas, abra la pestaña con las respuestas antes de copiar el enlace: "
               "el número <font name='Courier'>gid=...</font> al final indica qué pestaña se lee."], numbered=True),
      note("<b>Privacidad.</b> Las personas con el enlace pueden ver los nombres y las respuestas. Si el curso "
           "es sensible, vuelva a restringir el acceso a la hoja cuando termine la actividad. Al proyectar la "
           "aplicación en clase recuerde que muestra los nombres de los estudiantes.")]

s += [P("4. Paso 3: cargar los datos en la aplicación", h2),
      bullets(["Pegue el enlace en el cuadro <b>«Enlace a la hoja de respuestas»</b> de la barra lateral.",
               "Revise el resumen de la barra lateral: número de estudiantes, de películas, porcentaje de "
               "celdas calificadas y rango de fechas.",
               "<b>Desde (fecha) y Desde (hora):</b> conservan solo las respuestas a partir de esa fecha y hora "
               "(por defecto 00:00). Sirven para ignorar semestres anteriores si reutiliza el formulario, o para "
               "separar secciones que responden el mismo día: fije la hora de inicio de la sección.",
               "<b>Mínimo de películas calificadas:</b> excluye a quienes calificaron muy pocas películas "
               "(por defecto 4).",
               "<b>Recargar datos:</b> vuelve a leer la hoja para incluir respuestas nuevas. La aplicación también "
               "actualiza los datos automáticamente cada 5 minutos.",
               "Si aparece un cuadro de <b>«Avisos al leer la hoja»</b>, indica columnas o valores que no se "
               "pudieron interpretar (por ejemplo, una columna de correo electrónico). Se ignoran, pero conviene "
               "revisar que no sea una película."], numbered=True),
      P("<b>Descargar calificaciones:</b> el botón de la barra lateral descarga un archivo Excel (.xlsx) con una fila por estudiante "
        "y una columna por película (títulos en inglés si la película está en el mapeo del curso; 1 a 5; vacío = no la vio), aplicando la fecha y hora «Desde» y el mínimo de "
        "películas calificadas. Incluye los nombres: anonimícelos antes de compartir el archivo con los "
        "estudiantes."),
      P("En la barra lateral, el recuadro <b>«Películas del formulario»</b> muestra cada película con su número de "
        "calificaciones y su promedio, y permite descargar la lista de nombres (ver sección 6). El recuadro "
        "<b>«Estructura requerida del formulario»</b> resume lo explicado en el Paso 1.")]

s += [P("5. Pestaña «Compañeros»", h2),
      bullets(["<b>Buscar estudiante / Estudiante:</b> escriba parte del nombre y elija a la persona.",
               "<b>Compañeros más parecidos:</b> los 10 compañeros más cercanos, con su <i>distancia</i> "
               "(menor = más parecido) y el número de películas que ambos calificaron. El control "
               "<i>Mínimo de películas en común</i> evita que alguien que compartió solo 2 películas parezca "
               "idéntico por casualidad. Debajo se comparan las calificaciones del estudiante con las de sus "
               "tres compañeros más cercanos.",
               "<b>Películas que no ha visto:</b> para cada una se muestra la calificación predicha y los "
               "<i>k</i> compañeros (con sus calificaciones) que la originan. La predicción es el promedio de los "
               "<i>k</i> compañeros más cercanos que sí la vieron. Con <i>k</i> pequeño la predicción es ruidosa; "
               "con <i>k</i> grande se acerca al promedio de la película. Elija una película en "
               "«Detalle de una predicción» para ver el cálculo.",
               "<b>Mapa de calor:</b> la tabla completa de calificaciones (rojo = 1, verde = 5, blanco = no vista). "
               "La primera fila es el estudiante elegido y debajo van sus compañeros, del más al menos parecido."]),
      P("<b>Cómo se mide la distancia.</b> Es la distancia euclidiana calculada solo con las películas que ambas "
        "personas calificaron, reescalada por las películas que faltan. Es el mismo método de "
        "<font name='Courier'>KNNImputer</font> de scikit-learn: predecir las películas no vistas equivale a "
        "completar los valores faltantes de la tabla estudiantes × películas.")]

s += [P("6. Pestaña «MovieLens»: recomendar más allá del formulario", h2),
      P("MovieLens es una base de datos real de calificaciones (610 usuarios, 9.700 películas, principalmente de "
        "EE.UU., entre 1996 y 2018). Se usan sus usuarios como «vecinos» del estudiante para recomendar películas "
        "que <b>no</b> están en el formulario. Para esto la aplicación necesita saber qué película de MovieLens "
        "es cada película de su formulario, es decir, su <b>movieId</b>."),
      P("Si su formulario usa películas distintas a las del curso original, siga estos pasos:", h3),
      bullets(["Abra la pestaña «MovieLens», despliegue <b>«Mapeo de las películas del formulario a MovieLens»</b> "
               "y pulse <b>Descargar nombres (CSV)</b> (también está en la barra lateral). Obtiene un archivo con "
               "las columnas <font name='Courier'>title</font> y <font name='Courier'>movieId</font>.",
               "Complete la columna <font name='Courier'>movieId</font> <b>fuera de la aplicación</b> (en Excel o "
               "Google Sheets). Para encontrar el id: en <font name='Courier'>movielens.org</font> busque la "
               "película; el número al final de la dirección de su página "
               "(<font name='Courier'>movielens.org/movies/858</font>) es el movieId. También puede buscarla en "
               "el archivo <font name='Courier'>movies.csv</font> de «ml-latest-small», disponible en "
               "grouplens.org/datasets/movielens/latest/.",
               "Guarde el archivo como <b>CSV</b> y súbalo con <b>«Subir mapeo»</b>. El título debe coincidir "
               "con el del formulario (mayúsculas y minúsculas no importan).",
               "Revise el mensaje «N de M películas con movieId válido». Los avisos indican ids no numéricos, "
               "ids que no existen en MovieLens (solo está la versión pequeña), ids repetidos y títulos que no "
               "están en el formulario."], numbered=True),
      note("<b>El mapeo es temporal.</b> El archivo se usa solo durante su sesión y no se guarda: si recarga la "
           "página debe subirlo otra vez. No es necesario mapear todas las películas, pero cada película sin "
           "movieId se ignora en esta pestaña. Se necesitan varias películas mapeadas (idealmente 10 o más) para "
           "encontrar vecinos."),
      Spacer(1, 6),
      P("Qué muestra la pestaña", h3),
      bullets(["<b>Recomendaciones</b> para el estudiante elegido en «Compañeros»: películas populares de "
               "MovieLens (al menos 50 calificaciones) que no están en el formulario, con la calificación "
               "predicha. Se controlan con <i>k</i> (vecinos) y el número de recomendaciones.",
               "<b>Usuarios de MovieLens más parecidos:</b> los 10 usuarios más cercanos al estudiante, con su "
               "distancia y las películas del formulario que ambos calificaron. Sirven para entender de dónde "
               "vienen las recomendaciones; cada predicción usa, en rigor, a los <i>k</i> usuarios más "
               "cercanos que calificaron <i>esa</i> película.",
               "Los usuarios de MovieLens no son personas conocidas por el curso; sus gustos pueden diferir "
               "de los de sus estudiantes."])]

s += [P("7. Interpretar los resultados con cuidado", h2),
      bullets(["Con un curso de unos 90 estudiantes y unas 20 películas, las predicciones apenas superan el "
               "promedio de cada película. El método mejora cuando hay cientos de usuarios comparables; esa es "
               "justamente la lección de usar MovieLens.",
               "Una distancia pequeña con pocas películas en común es poco informativa: mire también esa columna.",
               "Las predicciones son promedios de unos pocos vecinos; no son «el gusto verdadero» de la persona."])]

s += [KeepTogether([P("8. Solución de problemas", h2),
      table([["Mensaje o síntoma", "Causa probable y solución"],
             ["«No se pudo acceder a la hoja» / «la hoja no es pública»",
              "La hoja no está compartida con «Cualquier persona con el enlace». Cambie el acceso a Lector "
              "(Paso 2) y pulse «Recargar datos»."],
             ["«El enlace no parece ser de una hoja de Google Sheets»",
              "Pegó el enlace del formulario (forms.gle) o un enlace de otro tipo. Use el de la hoja de "
              "respuestas."],
             ["Una columna aparece en «Avisos» y se ignora",
              "Sus respuestas no son una escala reconocida (Paso 1) o la columna no tiene respuestas. Si es una "
              "película, revise los textos de las opciones."],
             ["Todas las calificaciones salen vacías",
              "Los textos de las opciones no coinciden con los aceptados. Use los textos de la tabla del Paso 1 "
              "o una escala numérica de 1 a 5."],
             ["«Con estos filtros quedan menos de 3 estudiantes»",
              "Cambie la fecha «Desde» o baje el mínimo de películas calificadas."],
             ["«Ningún usuario de MovieLens calificó al menos N de las películas»",
              "Hay muy pocas películas con movieId o son muy poco conocidas. Agregue más ids al mapeo."],
             ["Faltan respuestas nuevas",
              "Pulse «Recargar datos» (la aplicación también se actualiza cada 5 minutos)."],
             ["Las columnas no son las esperadas",
              "Verifique el orden: marca temporal primero, nombre al final y las películas en medio."]],
            [6 * cm, 11 * cm])])]

s += [Spacer(1, 10),
      P("<b>Créditos y licencia de los datos.</b> Datos de MovieLens (ml-latest-small), GroupLens Research, "
        "University of Minnesota. F. Maxwell Harper y Joseph A. Konstan (2015). <i>The MovieLens Datasets: History "
        "and Context.</i> ACM Transactions on Interactive Intelligent Systems 5(4): 19:1-19:19. "
        "https://doi.org/10.1145/2827872. Uso educativo y de investigación; sin fines comerciales y sin "
        "respaldo de GroupLens.", small)]

doc = SimpleDocTemplate(OUT, pagesize=letter, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                        bottomMargin=2 * cm, title="Recomendador de películas - Guía para profesores",
                        author="Reasoning with Data, FEN Universidad de Chile")
doc.build(s, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
