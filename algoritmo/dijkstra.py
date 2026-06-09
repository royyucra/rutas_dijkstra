import heapq


def dijkstra(grafo, origen, destino):
    """
    Algoritmo de Dijkstra.
    Retorna:
        - ruta: lista de nodos en la ruta más corta
        - distancia: distancia total en km
        - pasos: historial de procesamiento [(nodo_actual, dist_acumulada)]
    """
    distancias = {nodo: float('inf') for nodo in grafo}
    distancias[origen] = 0
    previo = {nodo: None for nodo in grafo}
    heap = [(0, origen)]
    visitados = set()
    pasos = []

    while heap:
        dist_actual, nodo_actual = heapq.heappop(heap)

        if nodo_actual in visitados:
            continue
        visitados.add(nodo_actual)
        pasos.append((nodo_actual, dist_actual, set(visitados)))

        if nodo_actual == destino:
            break

        for vecino, peso in grafo[nodo_actual]:
            nueva_dist = dist_actual + peso
            if nueva_dist < distancias[vecino]:
                distancias[vecino] = nueva_dist
                previo[vecino] = nodo_actual
                heapq.heappush(heap, (nueva_dist, vecino))

    # Reconstruir ruta
    ruta = []
    nodo = destino
    while nodo is not None:
        ruta.append(nodo)
        nodo = previo[nodo]
    ruta.reverse()

    if ruta[0] != origen:
        return [], float('inf'), []

    return ruta, distancias[destino], pasos
