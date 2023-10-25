from animation import play_score, clear_screen
from airport import generate_random_airports
from player import init_player_state, load_player_state, save_player_state
from utils import database_execute, get_highest_score, calculate_score
from scene import shop, arrival, departure, end_game


# ---------------------
# MAIN GAME
# ---------------------

def game(connection, resume=False, debug=False):
    # ---------------------
    # CONFIG
    # ---------------------

    # plane
    # fuel consumption: kg/km,
    # speed: km/h,
    # emission: g/km
    # reward: euro/km

    plane_param = {"fuel_consumption": 1.2,
                   "speed": 800,
                   "emission": 0.1,
                   "reward": 1.2}

    arrival_param = {"hand_over_cost": 600,
                     "dice_bonus_percent": 4,

                     "treasure_value": 20000,
                     "detector_base_per_10k": 20,
                     "detector_bonus_per_10k": 50,

                     "dividend": 500}
    # every [dividend] km, add percentage to [fuel_back_percent]/[dice_bonus_percent]
    # for example: every 500km, increase 1 percentage to fuel back and dice bonus.

    shop_param = {"fuel_price": 0.8,
                  "win_money": 20000}

    score_param = {"money": 1,
                   "emission": 1,
                   "time": 0.01}

    time_limit_days = 5  # days in game
    init_money = 2000
    init_fuel = 0
    init_probability = 5
    num_of_airport = 30

    # ---------------------
    # GAME INIT (NEW GAME OR CONTINUE GAME)
    # ---------------------

    # new game or resume
    if not resume:
        # new game
        # input player name
        while True:
            print("\nHello, what's your name?")
            player_name = input("> ").strip()
            if player_name.isspace() or player_name == "":
                print("Enter your name please.")
            else:
                break

        time_limit = time_limit_days * 24 * 3600
        #
        current_airport_info = generate_random_airports(connection, num_of_airport)
        player_state = {"name": player_name, "money": init_money, "fuel": init_fuel, "emission": 0,
                        "location": current_airport_info["ident"], "probability": init_probability, "time": time_limit,
                        "treasure": 0, "reminder": 0, "score": 0, "finish": 0}
        init_player_state(connection, player_state)
    else:
        # resume, load from database
        # check is there resume
        sql_query = "SELECT screen_name, location, finish FROM game WHERE id=(SELECT MAX(id) FROM game)"
        sql_fetch = database_execute(connection, sql_query)
        is_finish = sql_fetch[0]["finish"]
        screen_name = sql_fetch[0]["screen_name"]
        if is_finish == 0:
            print(f"You have a game save whose name is {screen_name}, do you want to continue? (Y/n)")
            select = input("> ").strip()
            if select == "y" or select == "Y" or select == "":
                print("Game loaded, good luck!")
                input("(press Enter to continue)")
                clear_screen()
                player_state = load_player_state(connection, screen_name)
                player_state["name"] = screen_name
                sql_query = "SELECT name, country_name, visit FROM game_airport WHERE ident=%s"
                current_airport_info = database_execute(connection, sql_query, (player_state["location"],))[0]
                # reset last travel distance to 0, because we don't know that from game save
                current_airport_info["distance"] = 0
            else:
                print("Returning to main menu.")
                input("(press Enter to continue)")
                return 0
        else:
            print("Game save not found, returning to main menu")
            input("(press Enter to continue)")
            return 1

    # ---------------------
    # GAME START
    # ---------------------

    while True:
        # first step: go to shop
        end_type = shop(
            player_state=player_state,
            current_airport_info=current_airport_info,
            shop_param=shop_param)

        # save game in between
        save_player_state(connection, player_state)
        # check is game over
        if end_type != 0:
            end_game(end_type)
            break

        # second step: depart to next airport.
        end_type, current_airport_info = departure(
            connection=connection,
            current_airport_info=current_airport_info,
            shop_param=shop_param,
            plane_param=plane_param,
            player_state=player_state)

        # save game in between
        save_player_state(connection, player_state)
        # check is game over
        if end_type != 0:
            end_game(end_type)
            break

        # third step: arrive new airport
        arrival(
            current_airport_info=current_airport_info,
            arrival_param=arrival_param,
            player_state=player_state,
            shop_param=shop_param)

        # save game in between, (but no game over check here because game can't be over here)
        save_player_state(connection, player_state)

        # loop back to beginning

    # ---------------------
    # GAME END
    # ---------------------

    # out of loop game ended

    # high score
    if end_type == 1:
        last_high_score = get_highest_score(connection)
        score_dict, score = calculate_score(player_state, score_param)
        # set player's score when win
        player_state["score"] = score
        # play ending score animation
        if last_high_score < score:
            is_high_score = True
        else:
            is_high_score = False
        play_score(player_state, shop_param["fuel_price"], score_dict, is_high_score)
    else:
        # not win, no score
        player_state["score"] = 0
        print("Not calculating score because it's only for winner.")
        print("Try harder next time!")
        input("(press Enter to continue)")

    # set player finished game
    player_state["finish"] = 1
    # save all above to database
    save_player_state(connection, player_state)
