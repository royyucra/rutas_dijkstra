import folium
import os
import tempfile


def generar_mapa(ruta=None, visitados=None, origen=None, destino=None, departamentos=None, aristas=None):
    """
    Genera un mapa Folium con OpenStreetMap.
    - ruta: lista de nodos en la ruta más corta
    - visitados: set de nodos visitados por Dijkstra
    - origen, destino: strings
    Retorna la ruta al archivo HTML temporal.
    """
    if departamentos is None or aristas is None:
        return None

    ruta = ruta or []
    visitados = visitados or set()
    aristas_ruta = set()
    if len(ruta) >= 2:
        for i in range(len(ruta) - 1):
            aristas_ruta.add((ruta[i], ruta[i+1]))
            aristas_ruta.add((ruta[i+1], ruta[i]))

    # Centro del Perú
    mapa = folium.Map(
        location=[-9.19, -75.0],
        zoom_start=6,
        tiles="OpenStreetMap",
        control_scale=True
    )

    # Dibujar todas las aristas
    for a, b, _ in aristas:
        if a not in departamentos or b not in departamentos:
            continue
        la, loa = departamentos[a]
        lb, lob = departamentos[b]
        es_ruta = (a, b) in aristas_ruta

        folium.PolyLine(
            locations=[[la, loa], [lb, lob]],
            color="#E24B4A" if es_ruta else "#9E9E9E",
            weight=5 if es_ruta else 1.5,
            opacity=1.0 if es_ruta else 0.4,
            tooltip=f"{a} ↔ {b}" if es_ruta else None,
        ).add_to(mapa)

    # Dibujar nodos
    for dep, (lat, lon) in departamentos.items():
        es_origen  = dep == origen
        es_destino = dep == destino
        en_ruta    = dep in ruta
        visitado   = dep in visitados

        if es_origen or es_destino:
            color, radius, fill_opacity = "#FAC775", 12, 1.0
        elif en_ruta:
            color, radius, fill_opacity = "#E24B4A", 10, 1.0
        elif visitado:
            color, radius, fill_opacity = "#5599DD", 8, 0.8
        else:
            color, radius, fill_opacity = "#1D9E75", 7, 0.85

        icono = "🟡" if es_origen else ("🔴" if es_destino else "")
        popup_html = f"""
        <div style='font-family:sans-serif;font-size:13px;'>
          <b>{icono} {dep}</b><br>
          <span style='color:gray'>Lat: {lat:.4f}, Lon: {lon:.4f}</span>
          {'<br><b style="color:#E24B4A">✓ En ruta óptima</b>' if en_ruta else ''}
        </div>"""

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color="white",
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=fill_opacity,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=dep,
        ).add_to(mapa)

        # Etiqueta de texto
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:9px;font-weight:bold;color:#1a1a1a;'
                     f'text-shadow:1px 1px 2px white,-1px -1px 2px white;'
                     f'white-space:nowrap;margin-top:-22px;margin-left:10px">{dep}</div>',
                icon_size=(120, 20),
            )
        ).add_to(mapa)

    # Leyenda
    leyenda_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:9999;
                background:white;padding:12px 16px;border-radius:10px;
                box-shadow:0 2px 10px rgba(0,0,0,0.2);font-family:sans-serif;font-size:12px;">
      <b>Leyenda</b><br>
      <span style="color:#1D9E75">●</span> Departamento normal<br>
      <span style="color:#FAC775">●</span> Origen / Destino<br>
      <span style="color:#E24B4A">●</span> Ruta más corta<br>
      <span style="color:#5599DD">●</span> Visitado por Dijkstra<br>
      <span style="color:#9E9E9E">—</span> Conexión disponible<br>
      <span style="color:#E24B4A">—</span> Ruta óptima
    </div>"""
    mapa.get_root().html.add_child(folium.Element(leyenda_html))

    # Guardar en archivo temporal
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", prefix="mapa_peru_")
    mapa.save(tmp.name)
    return tmp.name
