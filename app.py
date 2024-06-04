import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import time
from PIL import Image
import csv
import io
import matplotlib.pyplot as plt

# Connexion à la base de données SQLite
conn = sqlite3.connect('tasks.db')
c = conn.cursor()

# Création des tables s'ils n'existent pas
c.execute('''CREATE TABLE IF NOT EXISTS tasks
             (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, due_date DATE, category TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS task_history
             (task_id INTEGER, action TEXT, timestamp TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS task_categories
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
conn.commit()



def column_exists(table_name, column_name):
    c.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in c.fetchall()]
    return column_name in columns

def add_category(category_name):
    if not column_exists('tasks', 'category'):
        c.execute("ALTER TABLE tasks ADD COLUMN category TEXT")
    c.execute("INSERT INTO task_categories (name) VALUES (?)", (category_name,))
    conn.commit()

# Vérifiez et ajoutez les colonnes si elles n'existent pas
if not column_exists('tasks', 'priority'):
    c.execute("ALTER TABLE tasks ADD COLUMN priority TEXT")
conn.commit()

def add_task(description, due_date, priority):
    with st.spinner('Ajout de la tâche en cours...'):
        time.sleep(2)  # Simulation d'une opération de traitement
        c.execute("INSERT INTO tasks (description, due_date, priority) VALUES (?, ?, ?)", (description, due_date, priority))
        conn.commit()

def get_tasks(sort_by):
    c.execute(f"SELECT * FROM tasks ORDER BY {sort_by}")
    return c.fetchall()

def update_task(task_id, description, due_date):
    with st.spinner('Mise à jour de la tâche en cours...'):
        time.sleep(2)  # Simulation d'une opération de traitement
        c.execute("UPDATE tasks SET description=?, due_date=? WHERE id=?", (description, due_date, task_id))
        log_task_history(task_id, 'update')
        conn.commit()

def delete_task(task_id):
    with st.spinner('Suppression de la tâche en cours...'):
        time.sleep(2)  # Simulation d'une opération de traitement
        c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        log_task_history(task_id, 'delete')
        conn.commit()

def toggle_task_completion(task_id):
    with st.spinner('Mise à jour du statut de la tâche en cours...'):
        time.sleep(2)  # Simulation d'une opération de traitement
        c.execute("UPDATE tasks SET completed = NOT completed WHERE id=?", (task_id,))
        log_task_history(task_id, 'toggle_completion')
        conn.commit()

def time_remaining(due_date):
    now = datetime.now()
    due_date = datetime.strptime(due_date, '%Y-%m-%d')
    delta = due_date - now
    if delta.days < 0:
        return "Tâche en retard"
    elif delta.days == 0:
        return f"{delta.seconds // 3600} heures restantes"
    else:
        return f"{delta.days} jours, {delta.seconds // 3600} heures restantes"

def play_sound():
    sound_html = """
    <audio autoplay>
        <source src="notification.mp3" type="audio/mpeg">
        Your browser does not support the audio element.
    </audio>
    """
    st.markdown(sound_html, unsafe_allow_html=True)

# Appelez cette fonction lorsqu'une notification est déclenchée
def notify_upcoming_tasks():
    now = datetime.now()
    for task in get_tasks('due_date'):
        task_id, description, due_date, completed, *rest = task
        due_date = datetime.strptime(due_date, '%Y-%m-%d')
        delta = due_date - now
        if delta.days == 0 and delta.seconds <= 86400 and not completed:  # Moins de 24 heures
            st.sidebar.warning(f"Tâche '{description}' à échéance dans moins de 24 heures!")
            play_sound()

def log_task_history(task_id, action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO task_history (task_id, action, timestamp) VALUES (?, ?, ?)", (task_id, action, timestamp))
    conn.commit()

def view_task_history(task_id):
    c.execute("SELECT * FROM task_history WHERE task_id=?", (task_id,))
    return c.fetchall()

def export_tasks_to_csv():
    tasks = get_tasks('due_date')
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Description', 'Due Date', 'Completed', 'Category'])
    writer.writerows(tasks)
    st.download_button(
        label="Télécharger les tâches en CSV",
        data=output.getvalue(),
        file_name='tasks_export.csv',
        mime='text/csv'
    )

def generate_statistics():
    total_tasks = len(get_tasks('id'))
    completed_tasks = len([task for task in get_tasks('id') if task[3]])
    overdue_tasks = len([task for task in get_tasks('due_date') if datetime.strptime(task[2], '%Y-%m-%d') < datetime.now() and not task[3]])
    st.sidebar.write(f'Tâches totales: {total_tasks}')
    st.sidebar.write(f'Tâches complétées: {completed_tasks}')
    st.sidebar.write(f'Tâches en retard: {overdue_tasks}')
    
    # Pie chart
    labels = 'Complétées', 'En retard', 'En cours'
    sizes = [completed_tasks, overdue_tasks, total_tasks - completed_tasks - overdue_tasks]
    colors = ['green', 'red', 'orange']
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.axis('equal')
    st.sidebar.pyplot(fig1)

# Générer des statistiques
generate_statistics()

def animated_text(text):
    words = text.split()
    animated_words = [f'<span style="animation: fadeIn 2s {i*1}s forwards;">{word}</span>' for i, word in enumerate(words)]
    animation_html = f"""
    <p>{' '.join(animated_words)}</p>
    <style>
    @keyframes fadeIn {{
        0% {{ opacity: 0; }}
        100% {{ opacity: 1; }}
    }}
    span {{ opacity: 0; }}
    </style>
    """
    st.markdown(animation_html, unsafe_allow_html=True)

# Utilisez cette fonction pour afficher du texte animé
animated_text('Bienvenue dans votre gestionnaire de tâches !!! ')

def display_task_with_priority(task):
    task_id, description, due_date, completed, priority = task[:5]
    col1, col2, col3, col4, col5, col6 = st.columns([0.1, 0.1, 0.3, 0.2, 0.1, 0.1])
    with col1:
        st.image(logo, width= 30) 
    with col2:
        if st.button('✅', key=f"complete_{task_id}"):
            toggle_task_completion(task_id)
            st.experimental_rerun()
    with col3:
        st.write(description)
    with col4:
        st.write(datetime.strptime(due_date, '%Y-%m-%d').strftime('%d/%m/%Y'))
    with col5:
        st.write(time_remaining(due_date))
    with col6:
        priority_badge = f"<span class='badge {priority}'>{priority}</span>"
        st.markdown(priority_badge, unsafe_allow_html=True)
        if st.button('❌', key=f"delete_{task_id}"):
            delete_task(task_id)
            st.experimental_rerun()

# CSS pour les badges
st.markdown("""
<style>
.badge {
    padding: 5px;
    border-radius: 5px;
    color: white;
    background-color: grey;
}
.badge.Haute {
    background-color: red;
}
.badge.Moyenne {
    background-color: orange;
}
.badge.Basse {
    background-color: green;
}
</style>
""", unsafe_allow_html=True)

# Interface utilisateur avec Streamlit
logo = Image.open("banner.png").resize((515, 512))
st.image(logo, use_column_width=True)

st.title('Gestionnaire de Tâches')
# Ajout d'un séparateur 

st.markdown("---")

# Ajouter une nouvelle tâche
st.sidebar.subheader("Ajouter une nouvelle tâche")

with st.sidebar.form(key="task_form"):
    task_description = st.text_input("Description de la tâche")
    due_date = st.date_input("Date limite")
    priority = st.selectbox("Priorité", ["Haute", "Moyenne", "Basse"])

    submit_button = st.form_submit_button("Ajouter")

if submit_button:
    add_task(task_description, due_date.strftime("%Y-%m-%d"), priority)
    st.sidebar.success("Tâche ajoutée avec succès!")

st.markdown("---")

# Ajouter une nouvelle catégorie
st.sidebar.subheader('Ajouter une nouvelle catégorie')
category_name = st.sidebar.text_input('Nom de la catégorie')
if st.sidebar.button('Ajouter catégorie'):
    add_category(category_name)
    st.sidebar.success('Catégorie ajoutée avec succès!')

# Filtres et tri
st.sidebar.subheader('Options de tri et de filtrage')
sort_by = st.sidebar.selectbox('Trier par', ['id', 'due_date', 'completed'])
tasks = get_tasks(sort_by)
st.sidebar.write('Nombre total de tâches:', len(tasks))


# Recherche avec mots-clés
st.sidebar.subheader('Recherche avec mots-clés')
keyword = st.sidebar.text_input('Mot-clé')
filtered_tasks = [task for task in tasks if keyword.lower() in task[1].lower()]
st.sidebar.write('Nombre de tâches correspondantes:', len(filtered_tasks))

# Notifications pour les tâches à échéance proche
notify_upcoming_tasks()

# Affichage des tâches :
st.subheader('Tâches en cours')
for task in filtered_tasks:
    if not task[3]:  # Si la tâche n'est pas complétée
        display_task_with_priority(task)


# Afficher les tâches terminées
st.subheader('Tâches terminées')
for task in filtered_tasks:
    task_id, description, due_date, completed, *rest = task
    if completed:
        st.write(f"{description} - Terminé le {datetime.strptime(due_date, '%Y-%m-%d').strftime('%d/%m/%Y')}")


# Gérer les tâches terminées
if st.sidebar.button('Supprimer les tâches terminées'):
    for task in filtered_tasks:
        if task[3]:  # Si la tâche est terminée
            delete_task(task[0])
    st.sidebar.success('Tâches terminées supprimées avec succès!')
    st.experimental_rerun()


# Afficher l'historique d'une tâche
st.sidebar.subheader('Afficher l\'historique d\'une tâche')
task_id_input = st.sidebar.number_input('ID de la tâche', min_value=1, step=1)
if st.sidebar.button('Afficher l\'historique des tâches'):
    history = view_task_history(task_id_input)
    if history:
        for entry in history:
            st.sidebar.write(f"{entry[1]} le {entry[2]}")
    else:
        st.sidebar.write('Aucun historique pour cette tâche.')


# Exporter les tâches en CSV
st.sidebar.subheader('Exporter les tâches')
if st.sidebar.button('Exporter vers CSV'):
    export_tasks_to_csv()

st.markdown("---")

# Image au pied de page
foot = Image.open("banner2.png").resize((900,150))
st.image(foot, use_column_width=True)
st.markdown("<h1 style='text-align: center; color: black;'> copyright 2024 ©</h1>", unsafe_allow_html=True)
st.markdown("---")
