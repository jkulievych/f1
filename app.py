import fastf1 as ff1
import fastf1.ergast
# Додаємо 'request' для форми
from flask import Flask, render_template, url_for, request
import pandas as pd
import os
import random
import matplotlib.pyplot as plt
import fastf1.plotting
from datetime import datetime  # Новий імпорт для отримання поточного року

app = Flask(__name__)

# --- FastF1 Cache Setup ---
try:
    ff1.Cache.enable_cache('f1_cache')
    print("Fast-F1 cache enabled at 'f1_cache'")
except Exception as e:
    print(f"Error enabling cache: {e}")


# --- Homepage (ПОВНІСТЮ ПЕРЕПИСАНО) ---
# --- Homepage (ПЕРЕПИСАНО З НАЙБІЛЬШ НАДІЙНИМ МЕТОДОМ) ---
# --- Homepage (СПРОЩЕНО: без подіуму) ---
@app.route('/')
def home():
    # Встановлюємо значення за замовчуванням
    driver_standings_list = []
    team_standings_list = []
    current_year = datetime.now().year  # 2025

    try:
        # --- 1. Отримуємо Топ-5 гонщиків та команд ---
        ergast = ff1.ergast.Ergast()

        try:
            driver_standings_df = ergast.get_driver_standings(current_year).content[0]
            driver_data = driver_standings_df[
                ['position', 'givenName', 'familyName', 'constructorNames', 'points', 'driverId', 'constructorIds']
            ].head(5)
            driver_standings_list = driver_data.to_dict('records')

            team_standings_df = ergast.get_constructor_standings(current_year).content[0]
            team_data = team_standings_df[
                ['position', 'constructorName', 'points', 'constructorId']
            ].head(5)
            team_standings_list = team_data.to_dict('records')
        except Exception as e:
            print(f"Could not load {current_year} standings (season may not have started): {e}")
            # Списки будуть порожніми, це нормально.

    except Exception as e:
        print(f"General error on homepage: {e}")

    # --- 2. Рендеримо шаблон 'home.html' (без подіуму) ---
    return render_template(
        'home.html',
        current_year=current_year,
        driver_standings_list=driver_standings_list,
        team_standings_list=team_standings_list
        # 'podium_list' та 'latest_session_name' видалено
    )

# --- Results Page (Ми її поки не чіпали) ---
@app.route('/results')
def show_results():
    try:
        session = ff1.get_session(2024, 'Monza', 'R')
        session.load(telemetry=False, weather=False)
        results = session.results

        results_table_data = results[['BroadcastName', 'TeamName', 'Position', 'Time', 'Status', 'Points']]
        results_table_data = results_table_data.rename(columns={'BroadcastName': 'Driver', 'TeamName': 'Team'})

        table_html = results_table_data.to_html(classes='data', index=False)
        return render_template(
            'results.html',
            session_name=f"{session.event['EventName']} {session.name}",
            table_html=table_html
        )
    except Exception as e:
        return f"Error loading session data: {e}", 500


# --- Standings Page (Без змін) ---
@app.route('/standings/<int:year>')
def show_standings(year):
    try:
        ergast = ff1.ergast.Ergast()

        driver_standings_df = ergast.get_driver_standings(year)
        driver_data = driver_standings_df.content[0][
            ['position', 'points', 'wins', 'givenName', 'familyName', 'constructorNames', 'driverId', 'constructorIds']]
        driver_list = driver_data.to_dict('records')

        team_standings_df = ergast.get_constructor_standings(year)
        team_data = team_standings_df.content[0][['position', 'points', 'wins', 'constructorName', 'constructorId']]
        team_list = team_data.to_dict('records')

        return render_template(
            'standings.html',
            year=year,
            driver_list=driver_list,
            team_list=team_list
        )
    except Exception as e:
        return f"Error loading Ergast data: {e}", 500


# --- Driver Profile Page (Без змін) ---
# TODO: Ця сторінка все ще "зашита" на 2024 рік
@app.route('/driver/<driver_id>')
def show_driver_profile(driver_id):
    try:
        ergast = ff1.ergast.Ergast()
        year = 2024  # TODO: Зробити цей рік динамічним
        results_df = ergast.get_driver_race_results(driver_id=driver_id, season=year)
        results_data = results_df.content[0]
        standings_df = ergast.get_driver_standings(season=year, driver_id=driver_id)
        standing_data = standings_df.content[0]
        if not standing_data.empty:
            driver_info = {'givenName': standing_data['givenName'].iloc[0],
                           'familyName': standing_data['familyName'].iloc[0], 'points': standing_data['points'].iloc[0],
                           'position': standing_data['position'].iloc[0], 'wins': standing_data['wins'].iloc[0],
                           'team': standing_data['constructorNames'].iloc[0]}
        else:
            driver_info = {'givenName': results_data['givenName'].iloc[0],
                           'familyName': results_data['familyName'].iloc[0], 'points': 0, 'position': 'N/A', 'wins': 0,
                           'team': results_data['constructorNames'].iloc[0]}
        results_table_data = results_data[['raceName', 'round', 'position', 'points', 'status']]
        results_table_html = results_table_data.to_html(classes='data', index=False)
        return render_template(
            'driver_profile.html',
            info=driver_info,
            results_table=results_table_html,
            year=year
        )
    except Exception as e:
        return f"Error loading driver data for {driver_id}: {e}", 500


# --- Team Profile Page (Без змін) ---
# TODO: Ця сторінка все ще "зашита" на 2024 рік
@app.route('/team/<constructor_id>')
def show_team_profile(constructor_id):
    try:
        ergast = ff1.ergast.Ergast()
        year = 2024  # TODO: Зробити цей рік динамічним
        team_standings_df = ergast.get_constructor_standings(season=year, constructor_id=constructor_id)
        team_info_df = team_standings_df.content[0]
        driver_standings_df = ergast.get_driver_standings(season=year, constructor_id=constructor_id)
        drivers_list = driver_standings_df.content[0].to_dict('records')
        if not team_info_df.empty:
            team_info = {'name': team_info_df['constructorName'].iloc[0], 'position': team_info_df['position'].iloc[0],
                         'points': team_info_df['points'].iloc[0], 'wins': team_info_df['wins'].iloc[0]}
        else:
            team_info = {'name': drivers_list[0]['constructorNames'][0], 'position': 'N/A', 'points': 0, 'wins': 0}
        return render_template(
            'team_profile.html',
            info=team_info,
            drivers=drivers_list,
            year=year
        )
    except Exception as e:
        return f"Error loading team data for {constructor_id}: {e}", 500


# --- Seasons List Page (Без змін) ---
@app.route('/seasons')
def show_seasons_list():
    current_year = datetime.now().year
    years_list = list(range(current_year, 2017, -1))

    return render_template(
        'seasons_list.html',
        years=years_list
    )


# --- Season Schedule Page (Без змін) ---
@app.route('/season/<int:year>')
def show_season_schedule(year):
    try:
        schedule = ff1.get_event_schedule(year)
        schedule_data = schedule[['RoundNumber', 'EventName', 'Country', 'EventDate']]
        schedule_list = schedule_data.to_dict('records')

        return render_template(
            'season_schedule.html',
            year=year,
            schedule_list=schedule_list
        )
    except Exception as e:
        return f"Error loading season schedule: {e}", 500


# --- ДЕТАЛІ ГОНКИ (Виправлено 'NaN'/'N/A' - НАДІЙНИЙ МЕТОД) ---
@app.route('/race/<int:year>/<race_name>')
def show_race_details(year, race_name):
    try:
        # --- 1. Отримуємо сесію (швидко, без .load()) ---
        session_R = ff1.get_session(year, race_name, 'R')

        # --- 2. Перевіряємо дату ---
        today = pd.Timestamp('today')

        event_date = session_R.event['EventDate']
        session_name = f"{session_R.event['EventName']} {year}"

        if event_date > today:
            # --- 3A. ЯКЩО ГОНКА В МАЙБУТНЬОМУ: Повертаємо "комунікатор" ---
            return f"""
            <head>
                <title>Race Not Started</title>
                <style>
                    body {{ font-family: -apple-system, sans-serif; margin: 20px; background: #f9f9f9; }} 
                    h1 {{ color: #e10600; }}
                    .message-box {{ width: 80%; margin: 30px auto; padding: 40px; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; text-align: center; }}
                    p {{ font-size: 1.3em; }}
                </style>
            </head>
            <body>
                <h1>{session_name}</h1>
                <div class="message-box">
                    <p>This event has not happened yet.</p>
                    <p>Data will be available after <strong>{event_date.strftime('%d %B %Y')}</strong>.</p>
                </div>
                <br>
                <a href="{url_for('show_season_schedule', year=year)}">Back to Season Schedule</a>
            </body>
            """

        # --- 3B. ЯКЩО ГОНКА В МИНУЛОМУ: Завантажуємо дані ---

        session_R.load(telemetry=False, weather=False, laps=True)

        #
        # ОСЬ ТУТ ВИПРАВЛЕННЯ (ГОНКА):
        # 1. Робимо .copy() ОДРАЗУ з ОРИГІНАЛУ
        race_results = session_R.results.copy()

        # 2. ФОРМАТУЄМО ПОВНУ КОПІЮ
        race_results['Position'] = race_results['Position'].apply(lambda x: int(x) if pd.notna(x) else 'N/A')
        race_results['Points'] = race_results['Points'].apply(lambda x: int(x) if pd.notna(x) else 0)

        def format_race_time(time_val):
            if pd.isna(time_val):
                # Це виправлення для Time: NaT (Not a Time) - це не те ж саме, що і Time (який є str)
                return 'N/A'
            if isinstance(time_val, pd.Timedelta):
                return str(time_val).split(' ')[-1][:-3]
            return str(time_val)  # 'Lapped', '+1 Lap' etc.

        race_results['Time'] = race_results['Time'].apply(format_race_time)

        # 3. ТІЛЬКИ ТЕПЕР обираємо колонки
        race_results_data = race_results[['BroadcastName', 'TeamName', 'Position', 'Time', 'Status', 'Points']]
        race_results_data = race_results_data.rename(columns={'BroadcastName': 'Driver', 'TeamName': 'Team'})
        race_results_table = race_results_data.to_html(classes='data', index=False)

        session_Q = ff1.get_session(year, race_name, 'Q')
        session_Q.load(telemetry=False)
        drivers_list = session_Q.laps['Driver'].unique()

        #
        # ОСЬ ТУТ ВИПРАВЛЕННЯ (КВАЛІФІКАЦІЯ):
        # 1. Робимо .copy() ОДРАЗУ
        qual_results = session_Q.results.copy()

        # 2. ФОРМАТУЄМО ПОВНУ КОПІЮ
        qual_results['Position'] = qual_results['Position'].apply(lambda x: int(x) if pd.notna(x) else 'N/A')

        def format_q_time(time_val):
            if pd.notna(time_val):
                return str(time_val).split(' ')[-1][:-3]
            else:
                return 'N/A'

        qual_results['Q1'] = qual_results['Q1'].apply(format_q_time)
        qual_results['Q2'] = qual_results['Q2'].apply(format_q_time)
        qual_results['Q3'] = qual_results['Q3'].apply(format_q_time)

        # 3. ТІЛЬКИ ТЕПЕР обираємо колонки
        qual_results_data = qual_results[['BroadcastName', 'TeamName', 'Position', 'Q1', 'Q2', 'Q3']]
        qual_results_data = qual_results_data.rename(columns={'BroadcastName': 'Driver', 'TeamName': 'Team'})
        qual_results_table = qual_results_data.to_html(classes='data', index=False)

        return render_template(
            'race_details.html',
            year=year,
            race_name=race_name,
            session_name=session_name,
            qual_results_table=qual_results_table,
            race_results_table=race_results_table,
            drivers_list=drivers_list
        )

    except Exception as e:
        # --- 4. ЯКЩО СТАЛАСЯ БУДЬ-ЯКА ІНША ПОМИЛКА ---
        error_message = f"Error loading race details for {race_name}: {e}"
        print(error_message)
        return f"""
            <head>
                <title>Error</title>
                <style>
                    body {{ font-family: -apple-system, sans-serif; margin: 20px; background: #f9f9f9; }} 
                    h1 {{ color: #e10600; }}
                    .message-box {{ width: 80%; margin: 30px auto; padding: 40px; background: #fff1f1; border: 2px solid #e1000; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; }}
                    p {{ font-size: 1.2em; }} code {{ background: #eee; padding: 3px; }}
                </style>
            </head>
            <body>
                <h1>An Error Occurred</h1>
                <div class="message-box">
                    <p>Sorry, the site encountered a problem.</p>
                    <p><strong>Details:</strong> <code>{e}</code></p>
                </div>
                <br>
                <a href="/">Back to Home</a>
            </body>
            """

# --- Plot Page (Оновлено для динамічного заголовка) ---
@app.route('/race/<int:year>/<race_name>/plot')
def show_race_plot(year, race_name):
    session_type = request.args.get('session_type', 'Q')
    driver_1 = request.args.get('d1', 'LEC')
    driver_2 = request.args.get('d2', 'SAI')

    try:
        # --- 1. Створюємо наш власний словник кольорів ---
        MANUAL_TEAM_COLORS = {
            # --- Сучасні команди (2024) ---
            "Red Bull Racing": "#0600EF", "Ferrari": "#DC0000",
            "McLaren": "#FF8700", "Mercedes": "#00D2BE",
            "Aston Martin": "#006F62", "Alpine": "#0090FF",
            "Williams": "#005AFF", "RB": "#0032FF",
            "Sauber": "#00E700", "Haas F1 Team": "#B6B6B6",

            # --- Старі команди (близько 2011) ---
            "Force India": "#FF8000", "Lotus Renault": "#FFD700",
            "Toro Rosso": "#0000FF", "Lotus": "#004F2D",
            "HRT": "#B0B0B0", "Marussia": "#B00000",
            "Virgin": "#D10000", "Caterham": "#005030"
        }

        # --- 2. Налаштування ---
        ff1.plotting.setup_mpl(misc_mpl_mods=False)
        static_folder = os.path.join(app.root_path, 'static')

        # --- 3. Завантажуємо сесію ---
        print(f"Loading {year} {race_name} {session_type} session...")
        session = ff1.get_session(year, race_name, session_type)
        session.load(telemetry=True, weather=False)

        # --- 4. Отримуємо дані телеметрії ---
        fastest_d1 = session.laps.pick_driver(driver_1).pick_fastest()
        fastest_d2 = session.laps.pick_driver(driver_2).pick_fastest()
        tel_d1 = fastest_d1.get_car_data().add_distance()
        tel_d2 = fastest_d2.get_car_data().add_distance()

        # 5. Отримуємо кольори
        team_d1 = fastest_d1['Team']
        team_d2 = fastest_d2['Team']
        color_d1 = MANUAL_TEAM_COLORS.get(team_d1, '#808080')
        color_d2 = MANUAL_TEAM_COLORS.get(team_d2, '#808080')

        # --- 6. Створюємо графік ---
        fig, ax = plt.subplots(figsize=(16, 9))

        ax.plot(tel_d1['Distance'], tel_d1['Speed'], color=color_d1, label=driver_1)
        ax.plot(tel_d2['Distance'], tel_d2['Speed'], color=color_d2, label=driver_2)

        session_name_full = f"{session.event.EventName} {year} ({session_type})"
        ax.set_title(f'Fastest Lap Telemetry - {session_name_full}')
        ax.set_xlabel('Distance (m)')
        ax.set_ylabel('Speed (km/h)')
        ax.legend()

        # --- 7. Зберігаємо графік ---
        plot_filename = 'telemetry_plot.png'
        plot_path = os.path.join(static_folder, plot_filename)
        plt.savefig(plot_path)
        plt.close(fig)
        print(f"Saved {session_type} plot to {plot_path}")

        # --- 8. Рендеримо шаблон ---
        return render_template(
            'race_plot.html',
            session_name=session_name_full,
            plot_filename=plot_filename,
            cache_buster=random.randint(1, 1000000),
            driver_1=driver_1,  # <--- ДОДАНО
            driver_2=driver_2  # <--- ДОДАНО
        )

    except Exception as e:
        # --- 4. ЯКЩО СТАЛАСЯ ПОМИЛКА: Повертаємо "комунікатор" ---
        error_message = f"Error loading race data for {race_name} ({session_type}): {e}"
        print(error_message)
        return f"""
            <head>
                <title>Error</title>
                <style>
                    body {{ font-family: -apple-system, sans-serif; margin: 20px; background: #f9f9f9; }} 
                    h1 {{ color: #e10600; }}
                    .message-box {{ width: 80%; margin: 30px auto; padding: 40px; background: #fff1f1; border: 2px solid #e10600; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; }}
                    p {{ font-size: 1.2em; }} code {{ background: #eee; padding: 3px; }}
                </style>
            </head>
            <body>
                <h1>An Error Occurred</h1>
                <div class="message-box">
                    <p>Sorry, the site encountered a problem.</p>
                    <p><strong>Details:</strong> <code>{e}</code></p>
                </div>
                <br>
                <a href="/">Back to Home</a>
            </body>
            """

if __name__ == '__main__':
    app.run(debug=True)