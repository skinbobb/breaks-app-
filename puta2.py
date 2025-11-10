import sqlite3
from itertools import combinations

# Definir las posiciones que deben ser cubiertas
posiciones = ['kassa', 'heren', 'dames']

# Definir las restricciones de cada individuo y su rol
restricciones = {
    'Dennis': {'posiciones': ['kassa', 'heren'], 'rol': 'manager'},
    'Gaby': {'posiciones': ['kassa', 'heren'], 'rol': 'manager'},
    'Sharon': {'posiciones': ['dames'], 'rol': 'staff'},
    'Bobb': {'posiciones': ['kassa', 'heren'], 'rol': 'staff'},
    'Jacq': {'posiciones': ['kassa', 'heren', 'dames'], 'rol': 'staff', 'extra_time': False},
    'Kim': {'posiciones': ['kassa', 'heren', 'dames'], 'rol': 'staff', 'extra_time': False},
    'Melis': {'posiciones': ['dames'], 'rol': 'staff'},
    'Delana': {'posiciones': ['kassa', 'heren', 'dames'], 'rol': 'staff'},
    'Domingo': {'posiciones': ['heren'], 'rol': 'staff'},
    'Lau': {'posiciones': ['heren', 'dames'], 'rol': 'staff'},
}

# Definir la disponibilidad diaria de los trabajadores
disponibilidad_diaria = {
    'Dinsdag': ['Dennis', 'Gaby', 'Bobb', 'Delana', 'Melis', 'Sharon'],
    'Woensdag': ['Dennis', 'Gaby', 'Bobb', 'Sharon', 'Delana', 'Kim', 'Jacq'],
    'Donderdag': ['Dennis', 'Gaby', 'Bobb', 'Kim', 'Delana', 'Melis', 'Jacq'],
    'Vrijdag': ['Dennis', 'Gaby', 'Bobb', 'Sharon', 'Delana', 'Kim', 'Melis', 'Jacq'],
    'Zaterdag': ['Dennis', 'Gaby', 'Bobb', 'Delana', 'Kim', 'Melis', 'Domingo', 'Lau'],
    'Zondag': [],
}

# Definir la cantidad de personas necesarias por posición para cada día
necesidades_diarias = {
    'Dinsdag': {'kassa': 1, 'heren': 2, 'dames': 2},
    'Woensdag': {'kassa': 1, 'heren': 2, 'dames': 2},
    'Donderdag': {'kassa': 1, 'heren': 2, 'dames': 2},
    'Vrijdag': {'kassa': 1, 'heren': 2, 'dames': 2},
    'Zaterdag': {'kassa': 2, 'heren': 2, 'dames': 1},
    'Zondag': {'kassa': 0, 'heren': 0, 'dames': 0},
}

def inicializar_db():
    conn = sqlite3.connect('horarios.db')
    c = conn.cursor()

    # Crear tabla restricciones
    c.execute('''CREATE TABLE IF NOT EXISTS restricciones (
                    persona TEXT PRIMARY KEY,
                    posiciones TEXT,
                    rol TEXT,
                    extra_time BOOLEAN
                )''')

    # Crear tabla disponibilidad
    c.execute('''CREATE TABLE IF NOT EXISTS disponibilidad (
                    dia TEXT,
                    personas TEXT
                )''')

    # Crear tabla necesidades
    c.execute('''CREATE TABLE IF NOT EXISTS necesidades (
                    dia TEXT,
                    posicion TEXT,
                    cantidad INTEGER
                )''')

    # Crear tabla grupos
    c.execute('''CREATE TABLE IF NOT EXISTS grupos (
                    id INTEGER PRIMARY KEY,
                    dia TEXT,
                    grupo_num INTEGER,
                    personas TEXT
                )''')

    # Insertar datos en restricciones
    for persona, data in restricciones.items():
        posiciones_str = ','.join(data['posiciones'])
        extra_time = data.get('extra_time', True)  # Default True if not specified
        c.execute('INSERT OR REPLACE INTO restricciones VALUES (?, ?, ?, ?)',
                  (persona, posiciones_str, data['rol'], extra_time))

    # Insertar datos en disponibilidad
    for dia, personas in disponibilidad_diaria.items():
        personas_str = ','.join(personas)
        c.execute('INSERT OR REPLACE INTO disponibilidad VALUES (?, ?)', (dia, personas_str))

    # Insertar datos en necesidades
    for dia, needs in necesidades_diarias.items():
        for posicion, cantidad in needs.items():
            c.execute('INSERT OR REPLACE INTO necesidades VALUES (?, ?, ?)', (dia, posicion, cantidad))

    conn.commit()
    conn.close()

def cargar_datos_desde_db():
    conn = sqlite3.connect('horarios.db')
    c = conn.cursor()

    # Cargar restricciones
    restricciones_db = {}
    for row in c.execute('SELECT * FROM restricciones'):
        persona, posiciones_str, rol, extra_time = row
        posiciones = posiciones_str.split(',')
        restricciones_db[persona] = {'posiciones': posiciones, 'rol': rol}
        if not extra_time:
            restricciones_db[persona]['extra_time'] = False

    # Cargar disponibilidad
    disponibilidad_db = {}
    for row in c.execute('SELECT * FROM disponibilidad'):
        dia, personas_str = row
        personas = personas_str.split(',') if personas_str else []
        disponibilidad_db[dia] = personas

    # Cargar necesidades
    necesidades_db = {}
    for row in c.execute('SELECT * FROM necesidades'):
        dia, posicion, cantidad = row
        if dia not in necesidades_db:
            necesidades_db[dia] = {}
        necesidades_db[dia][posicion] = cantidad

    conn.close()
    return restricciones_db, disponibilidad_db, necesidades_db

# Inicializar la base de datos y cargar datos
inicializar_db()
restricciones, disponibilidad_diaria, necesidades_diarias = cargar_datos_desde_db()

def es_grupo_valido(grupo, posiciones, restricciones, dia):
    cubiertas = {posicion: 0 for posicion in posiciones}
    tiene_manager = False
    for persona in grupo:
        for posicion in restricciones[persona]['posiciones']:
            if posicion in cubiertas:
                cubiertas[posicion] += 1
        if restricciones[persona]['rol'] == 'manager':
            tiene_manager = True
    return all(cubiertas[posicion] >= necesidades_diarias[dia][posicion] for posicion in posiciones) and tiene_manager

def generar_grupos_diarios(posiciones, restricciones, disponibilidad):
    limpiar_grupos()
    for dia, personas in disponibilidad.items():
        print(f"\nGrupos para {dia}:")
        num_grupos = 3 if dia == 'Zaterdag' else 2
        contador = 0
        for combinacion in combinations(personas, len(personas) // num_grupos):
            if es_grupo_valido(combinacion, posiciones, restricciones, dia):
                restantes = [p for p in personas if p not in combinacion]
                if dia == 'Vrijdag':
                    # Asegurar que Kim y Jacq estén en el segundo grupo
                    if 'Kim' not in restantes or 'Jacq' not in restantes:
                        continue
                for sub_combinacion in combinations(restantes, len(restantes) // (num_grupos - 1)):
                    if es_grupo_valido(sub_combinacion, posiciones, restricciones, dia):
                        if num_grupos == 3:
                            # Para el sábado, generar un tercer grupo
                            ultimos = [p for p in restantes if p not in sub_combinacion]
                            for tercer_grupo in combinations(ultimos, len(ultimos)):
                                if es_grupo_valido(tercer_grupo, posiciones, restricciones, dia):
                                    print(f"Grupo 1: {combinacion}")
                                    print(f"Grupo 2: {sub_combinacion}")
                                    print(f"Grupo 3: {tercer_grupo}")
                                    contador += 1
                                    if contador == 3:  # Limitar a 3 opciones por día
                                        break
                        else:
                            print(f"Grupo 1: {combinacion}")
                            print(f"Grupo 2: {sub_combinacion}")
                            guardar_grupo(dia, 1, combinacion)
                            guardar_grupo(dia, 2, sub_combinacion)
                            contador += 1
                            if contador == 3:  # Limitar a 3 opciones por día
                                break
                if contador == 3:
                    break

def limpiar_grupos(dia=None):
    conn = sqlite3.connect('horarios.db')
    c = conn.cursor()
    if dia:
        c.execute('DELETE FROM grupos WHERE dia = ?', (dia,))
    else:
        c.execute('DELETE FROM grupos')
    conn.commit()
    conn.close()

def guardar_grupo(dia, grupo_num, personas):
    conn = sqlite3.connect('horarios.db')
    c = conn.cursor()
    personas_str = ','.join(personas)
    c.execute('INSERT INTO grupos (dia, grupo_num, personas) VALUES (?, ?, ?)', (dia, grupo_num, personas_str))
    conn.commit()
    conn.close()

def ver_grupos_guardados():
    conn = sqlite3.connect('horarios.db')
    c = conn.cursor()
    grupos = c.execute('SELECT dia, grupo_num, personas FROM grupos ORDER BY dia, grupo_num').fetchall()
    conn.close()
    if not grupos:
        print("No hay grupos guardados.")
        return
    current_dia = None
    for dia, grupo_num, personas_str in grupos:
        if dia != current_dia:
            print(f"\nGrupos para {dia}:")
            current_dia = dia
        personas = personas_str.split(',')
        print(f"Grupo {grupo_num}: {personas}")

def generar_grupos_dia_especifico(dia, posiciones, restricciones, disponibilidad):
    if dia not in disponibilidad:
        print(f"Día {dia} no encontrado en la disponibilidad.")
        return
    limpiar_grupos(dia)
    personas = disponibilidad[dia]
    print(f"\nGrupos para {dia}:")
    num_grupos = 3 if dia == 'Zaterdag' else 2
    contador = 0
    for combinacion in combinations(personas, len(personas) // num_grupos):
        if es_grupo_valido(combinacion, posiciones, restricciones, dia):
            restantes = [p for p in personas if p not in combinacion]
            if dia == 'Vrijdag':
                # Asegurar que Kim y Jacq estén en el segundo grupo
                if 'Kim' not in restantes or 'Jacq' not in restantes:
                    continue
            for sub_combinacion in combinations(restantes, len(restantes) // (num_grupos - 1)):
                if es_grupo_valido(sub_combinacion, posiciones, restricciones, dia):
                    if num_grupos == 3:
                        # Para el sábado, generar un tercer grupo
                        ultimos = [p for p in restantes if p not in sub_combinacion]
                        for tercer_grupo in combinations(ultimos, len(ultimos)):
                            if es_grupo_valido(tercer_grupo, posiciones, restricciones, dia):
                                print(f"Grupo 1: {combinacion}")
                                print(f"Grupo 2: {sub_combinacion}")
                                print(f"Grupo 3: {tercer_grupo}")
                                guardar_grupo(dia, 1, combinacion)
                                guardar_grupo(dia, 2, sub_combinacion)
                                guardar_grupo(dia, 3, tercer_grupo)
                                contador += 1
                                if contador == 3:  # Limitar a 3 opciones por día
                                    break
                    else:
                        print(f"Grupo 1: {combinacion}")
                        print(f"Grupo 2: {sub_combinacion}")
                        guardar_grupo(dia, 1, combinacion)
                        guardar_grupo(dia, 2, sub_combinacion)
                        contador += 1
                        if contador == 3:  # Limitar a 3 opciones por día
                            break
            if contador == 3:
                break

# Bucle interactivo
while True:
    print("\nOpciones:")
    print("1. Generar grupos para todos los días")
    print("2. Generar grupos para un día específico")
    print("3. Ver grupos guardados")
    print("4. Salir")
    opcion = input("Elige una opción (1-4): ").strip()

    if opcion == '1':
        generar_grupos_diarios(posiciones, restricciones, disponibilidad_diaria)
    elif opcion == '2':
        dia = input("Ingresa el día (ej. Dinsdag, Woensdag, etc.): ").strip()
        generar_grupos_dia_especifico(dia, posiciones, restricciones, disponibilidad_diaria)
    elif opcion == '3':
        ver_grupos_guardados()
    elif opcion == '4':
        print("¡Hasta luego!")
        break
    else:
        print("Opción no válida. Inténtalo de nuevo.")
