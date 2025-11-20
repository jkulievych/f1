import fastf1 as ff1
import fastf1.ergast
# Додаємо 'request' для форми
from flask import Flask, render_template, url_for, request
import pandas as pd
import os
import random
import matplotlib.pyplot as plt
import fastf1.plotting
from datetime import datetime
from timple.timedelta import strftimedelta
from fastf1.core import Laps
import seaborn as sns

app = Flask(__name__)

# --- Словник кольорів (глобальний) ---
MANUAL_TEAM_COLORS = {
    "Red Bull Racing": "#0600EF", "Ferrari": "#DC0000",
    "McLaren": "#FF8700", "Mercedes": "#00D2BE",
    "Aston Martin": "#006F62", "Alpine": "#0090FF",
    "Williams": "#005AFF", "RB": "#0032FF",
    "Sauber": "#00E700", "Haas F1 Team": "#B6B6B6",
    "Force India": "#FF8000", "Lotus Renault": "#FFD700",
    "Toro Rosso": "#0000FF", "Lotus": "#004F2D",
    "HRT": "#B0B0B0", "Marussia": "#B00000",
    "Virgin": "#D10000", "Caterham": "#005030"
}

# --- FastF1 Cache Setup ---
try:
    ff1.Cache.enable_cache('f1_cache')
    print("Fast-F1 cache enabled at 'f1_cache'")
except Exception as e:
    print(f"Error enabling cache: {e}")


# --- Homepage (Без змін) ---
@app.route('/')
def home():
    driver_standings_list = []
    team_standings_list = []
    current_year = datetime.now().year

    try:
        ergast = ff1.ergast.Ergast()
        try:
            driver_standings_df = ergast.get_driver_standings(current_year).content[0]
            driver_data = driver_standings_df[
                ['position', 'givenName', 'familyName', 'constructorNames', 'points']
            ].head(5)
            driver_standings_list = driver_data.to_dict('records')

            team_standings_df = ergast.get_constructor_standings(current_year).content[0]
            team_data = team_standings_df[
                ['position', 'constructorName', 'points']
            ].head(5)
            team_standings_list = team_data.to_dict('records')
        except Exception as e:
            print(f"Could not load {current_year} standings (season may not have started): {e}")
    except Exception as e:
        print(f"General error on homepage: {e}")

    return render_template(
        'home.html',
        current_year=current_year,
        driver_standings_list=driver_standings_list,
        team_standings_list=team_standings_list
    )


# --- Results Page (Без змін) ---
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
        error_message = f"Error loading results data: {e}"
        print(error_message)
        return render_template('error.html', error_message=error_message)


# --- Standings Page (Без змін) ---
@app.route('/standings/<int:year>')
def show_standings(year):
    try:
        ergast = ff1.ergast.Ergast()
        driver_standings_df = ergast.get_driver_standings(year)
        driver_data = driver_standings_df.content[0][
            ['position', 'points', 'wins', 'givenName', 'familyName', 'constructorNames']]
        driver_list = driver_data.to_dict('records')
        team_standings_df = ergast.get_constructor_standings(year)
        team_data = team_standings_df.content[0][['position', 'points', 'wins', 'constructorName']]
        team_list = team_data.to_dict('records')
        return render_template(
            'standings.html',
            year=year,
            driver_list=driver_list,
            team_list=team_list
        )
    except Exception as e:
        error_message = f"Error loading standings data for {year}: {e}"
        print(error_message)
        return render_template('error.html', error_message=error_message)


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
        error_message = f"Error loading season schedule for {year}: {e}"
        print(error_message)
        return render_template('error.html', error_message=error_message)


# --- ДЕТАЛІ ГОНКИ (СПРОЩЕНО: лише таблиці) ---
@app.route('/race/<int:year>/<race_name>')
def show_race_details(year, race_name):
    try:
        session_R = ff1.get_session(year, race_name, 'R')
        today = pd.Timestamp('today')
        event_date = session_R.event['EventDate']
        session_name = f"{session_R.event['EventName']} {year}"

        if event_date > today:
            return f"""
            <head><title>Race Not Started</title>
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
                <br><a href="{url_for('show_season_schedule', year=year)}">Back to Season Schedule</a>
            </body>
            """

        # --- ГОНКА (лише для таблиці) ---
        session_R.load(telemetry=False, weather=False, laps=True)
        race_results_df = session_R.results.copy()
        race_results_df['Position'] = race_results_df['Position'].apply(lambda x: int(x) if pd.notna(x) else 'N/A')
        race_results_df['Points'] = race_results_df['Points'].apply(lambda x: int(x) if pd.notna(x) else 0)

        def format_race_time(time_val):
            if pd.isna(time_val): return 'N/A'
            if isinstance(time_val, pd.Timedelta): return str(time_val).split(' ')[-1][:-3]
            return str(time_val)

        race_results_df['Time'] = race_results_df['Time'].apply(format_race_time)
        race_results_df['Driver'] = race_results_df['BroadcastName']
        race_results_df['Team'] = race_results_df['TeamName']
        race_results_table = race_results_df[['Driver', 'Team', 'Position', 'Time', 'Status', 'Points']].to_html(
            classes='data', index=False)

        # --- КВАЛІФІКАЦІЯ (лише для таблиці та списку гонщиків) ---
        session_Q = ff1.get_session(year, race_name, 'Q')
        session_Q.load(telemetry=False)
        drivers_list = session_Q.laps['Driver'].unique()
        qual_results_df = session_Q.results.copy()
        qual_results_df['Position'] = qual_results_df['Position'].apply(lambda x: int(x) if pd.notna(x) else 'N/A')

        def format_q_time(time_val):
            if pd.notna(time_val):
                return str(time_val).split(' ')[-1][:-3]
            else:
                return 'N/A'

        qual_results_df['Q1'] = qual_results_df['Q1'].apply(format_q_time)
        qual_results_df['Q2'] = qual_results_df['Q2'].apply(format_q_time)
        qual_results_df['Q3'] = qual_results_df['Q3'].apply(format_q_time)
        qual_results_df['Driver'] = qual_results_df['BroadcastName']
        qual_results_df['Team'] = qual_results_df['TeamName']
        qual_results_table = qual_results_df[['Driver', 'Team', 'Position', 'Q1', 'Q2', 'Q3']].to_html(classes='data',
                                                                                                       index=False)

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
        error_message = f"Error loading race details for {race_name}: {e}"
        print(error_message)
        return f"""
            <head><title>Error</title>
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
                <br><a href="/">Back to Home</a>
            </body>
            """


# --- Plot Page (Телеметрія - без змін) ---
@app.route('/race/<int:year>/<race_name>/plot/telemetry')
def show_race_plot(year, race_name):
    session_type = request.args.get('session_type', 'Q')
    driver_1 = request.args.get('d1', 'LEC')
    driver_2 = request.args.get('d2', 'SAI')

    try:
        fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme=None)
        static_folder = os.path.join(app.root_path, 'static')
        session = ff1.get_session(year, race_name, session_type)
        session.load(telemetry=True, weather=False)
        fastest_d1 = session.laps.pick_driver(driver_1).pick_fastest()
        fastest_d2 = session.laps.pick_driver(driver_2).pick_fastest()
        tel_d1 = fastest_d1.get_car_data().add_distance()
        tel_d2 = fastest_d2.get_car_data().add_distance()
        team_d1 = fastest_d1['Team']
        team_d2 = fastest_d2['Team']
        color_d1 = MANUAL_TEAM_COLORS.get(team_d1, '#808080')
        color_d2 = MANUAL_TEAM_COLORS.get(team_d2, '#808080')
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.plot(tel_d1['Distance'], tel_d1['Speed'], color=color_d1, label=driver_1)
        ax.plot(tel_d2['Distance'], tel_d2['Speed'], color=color_d2, label=driver_2)
        session_name_full = f"{session.event.EventName} {year} ({session_type})"
        ax.set_title(f'Fastest Lap Telemetry - {session_name_full}')
        ax.set_xlabel('Distance (m)')
        ax.set_ylabel('Speed (km/h)')
        ax.legend()
        plot_filename = 'telemetry_plot.png'
        plot_path = os.path.join(static_folder, plot_filename)
        plt.savefig(plot_path)
        plt.close(fig)
        return render_template(
            'race_plot.html',
            session_name=session_name_full,
            plot_filename=plot_filename,
            cache_buster=random.randint(1, 1000000),
            driver_1=driver_1,
            driver_2=driver_2
        )
    except Exception as e:
        error_message = f"Error loading race data for {race_name} ({session_type}): {e}"
        print(error_message)
        return f"""
            <head><title>Error</title>
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
                <br><a href="/">Back to Home</a>
            </body>
            """


#
# --- Графік "Qualifying results overview" (Без змін) ---
#
@app.route('/race/<int:year>/<race_name>/plot/qualifying')
def show_qualifying_plot(year, race_name):
    try:
        static_folder = os.path.join(app.root_path, 'static')

        session_Q = ff1.get_session(year, race_name, 'Q')
        session_Q.load(telemetry=False)
        drivers_list = session_Q.laps['Driver'].unique()

        fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme=None)

        list_fastest_laps = list()
        for drv in drivers_list:
            drvs_fastest_lap = session_Q.laps.pick_driver(drv).pick_fastest()
            list_fastest_laps.append(drvs_fastest_lap)
        fastest_laps = Laps(list_fastest_laps).sort_values(by='LapTime').reset_index(drop=True)

        pole_lap = fastest_laps.pick_fastest()
        fastest_laps['LapTimeDelta'] = fastest_laps['LapTime'] - pole_lap['LapTime']

        team_colors = [MANUAL_TEAM_COLORS.get(lap_data['Team'], '#808080') for index, lap_data in
                       fastest_laps.iterlaps()]

        fig, ax = plt.subplots()
        ax.barh(fastest_laps.index, fastest_laps['LapTimeDelta'],
                color=team_colors, edgecolor='grey')
        ax.set_yticks(fastest_laps.index)
        ax.set_yticklabels(fastest_laps['Driver'])
        ax.invert_yaxis()
        ax.set_axisbelow(True)
        ax.xaxis.grid(True, which='major', linestyle='--', color='black', zorder=-1000)

        lap_time_string = strftimedelta(pole_lap['LapTime'], '%m:%s.%ms')
        plot_title = f"{session_Q.event['EventName']} {session_Q.event.year} Qualifying\n" \
                     f"Fastest Lap: {lap_time_string} ({pole_lap['Driver']})"
        plt.suptitle(plot_title)

        qual_plot_filename = 'qualifying_overview_plot.png'
        qual_plot_path = os.path.join(static_folder, qual_plot_filename)
        plt.savefig(qual_plot_path)
        plt.close(fig)

        return render_template(
            'race_plot.html',
            session_name=plot_title,
            plot_filename=qual_plot_filename,
            cache_buster=random.randint(1, 1000000),
            driver_1=pole_lap['Driver'],
            driver_2=""
        )
    except Exception as e:
        error_message = f"Error loading qualifying plot for {race_name}: {e}"
        print(error_message)
        return f"""
            <head><title>Error</title>
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
                <br><a href="/">Back to Home</a>
            </body>
            """


#
# --- НОВА ФУНКЦІЯ: Графік "Team Pace Comparison" ---
#
@app.route('/race/<int:year>/<race_name>/plot/pace')
def show_pace_plot(year, race_name):
    try:
        static_folder = os.path.join(app.root_path, 'static')

        session_R = ff1.get_session(year, race_name, 'R')
        session_R.load(telemetry=False, weather=False, laps=True)

        laps = session_R.laps.pick_quicklaps()
        transformed_laps = laps.copy()
        transformed_laps.loc[:, "LapTime (s)"] = laps["LapTime"].dt.total_seconds()

        team_order = (
            transformed_laps[["Team", "LapTime (s)"]]
            .groupby("Team")
            .median()["LapTime (s)"]
            .sort_values()
            .index
        )

        team_palette = {team: MANUAL_TEAM_COLORS.get(team, '#808080') for team in team_order}

        fastf1.plotting.setup_mpl(mpl_timedelta_support=False, color_scheme='fastf1')

        fig, ax = plt.subplots(figsize=(15, 10))
        sns.boxplot(
            data=transformed_laps, x="Team", y="LapTime (s)", hue="Team",
            order=team_order, palette=team_palette,
            whiskerprops=dict(color="white"), boxprops=dict(edgecolor="white"),
            medianprops=dict(color="grey"), capprops=dict(color="white"),
        )

        plot_title = f"{session_R.event['EventName']} {year} - Team Race Pace"
        plt.title(plot_title)
        plt.grid(visible=False)
        ax.set(xlabel=None, ylabel="Lap Time (s)")

        pace_plot_filename = 'team_pace_plot.png'
        pace_plot_path = os.path.join(static_folder, pace_plot_filename)
        plt.savefig(pace_plot_path, facecolor='black')
        plt.close(fig)

        return render_template(
            'race_plot.html',
            session_name=plot_title,
            plot_filename=pace_plot_filename,
            cache_buster=random.randint(1, 1000000),
            driver_1="Team Pace",
            driver_2=""
        )
    except Exception as e:
        error_message = f"Error loading pace plot for {race_name}: {e}"
        print(error_message)
        return f"""
            <head><title>Error</title>
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
                <br><a href="/">Back to Home</a>
            </body>
            """


# --- НОВА ФУНКЦІЯ: Графік "Tyre Strategy" (ВИПРАВЛЕНО 'missing session') ---
@app.route('/race/<int:year>/<race_name>/plot/strategy')
def show_strategy_plot(year, race_name):
    try:
        static_folder = os.path.join(app.root_path, 'static')

        session_R = ff1.get_session(year, race_name, 'R')
        session_R.load(telemetry=False, weather=False, laps=True)
        laps_R = session_R.laps

        # Отримуємо результати гонки, щоб відсортувати гонщиків
        results_df = session_R.results.copy()

        # Використовуємо 'Abbreviation' (яка містить 'PER', 'VER')
        drivers_in_order = results_df.sort_values(by='Position')['Abbreviation'].tolist()
        drivers_in_order = [drv for drv in drivers_in_order if drv is not None]

        stints = laps_R[["Driver", "Stint", "Compound", "LapNumber"]]
        stints = stints.groupby(["Driver", "Stint", "Compound"])
        stints = stints.count().reset_index()
        stints = stints.rename(columns={"LapNumber": "StintLength"})

        fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme=None)

        fig, ax = plt.subplots(figsize=(7, 10))

        for driver in drivers_in_order:  # Малюємо в порядку фінішу
            driver_stints = stints.loc[stints["Driver"] == driver]
            previous_stint_end = 0
            for idx, row in driver_stints.iterrows():
                #
                # ОСЬ ТУТ ВИПРАВЛЕННЯ:
                #
                # Додаємо 'session=session_R'
                compound_color = fastf1.plotting.get_compound_color(row["Compound"], session=session_R)

                plt.barh(
                    y=driver,
                    width=row["StintLength"],
                    left=previous_stint_end,
                    color=compound_color,
                    edgecolor="black",
                    fill=True
                )
                previous_stint_end += row["StintLength"]

        plot_title = f"{session_R.event['EventName']} {year} Strategies"
        plt.title(plot_title)
        plt.xlabel("Lap Number")
        plt.grid(False)
        ax.invert_yaxis()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        plt.tight_layout()

        strategy_plot_filename = f'strategy_plot.png'
        strategy_plot_path = os.path.join(static_folder, strategy_plot_filename)
        plt.savefig(strategy_plot_path)
        plt.close(fig)

        return render_template(
            'race_plot.html',
            session_name=plot_title,
            plot_filename=strategy_plot_filename,
            cache_buster=random.randint(1, 1000000),
            driver_1="Tyre Strategy",
            driver_2=""
        )
    except Exception as e:
        error_message = f"Error loading strategy plot for {race_name}: {e}"
        print(error_message)
        return f"""
            <head><title>Error</title>
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
                <br><a href="/">Back to Home</a>
            </body>
            """


if __name__ == '__main__':
    app.run(debug=True)