import mysql.connector


class Database:
    def __init__(self, config):
        self.connection = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            autocommit=True)

    def query(self, query, parameter=None):
        # reconnect if connection is lost
        try:
            cursor = self.connection.cursor(dictionary=True)
        except mysql.connector.errors.OperationalError:
            self.reconnect()
            cursor = self.connection.cursor(dictionary=True)

        # set parameter to None if it is not provided
        if parameter is None:
            cursor.execute(query)
        else:
            # convert parameter to tuple if it is not
            if not isinstance(parameter, tuple):
                parameter = (parameter,)
            cursor.execute(query, parameter)
        response = cursor.fetchall()
        return response

    def reconnect(self):
        self.connection.reconnect()


def second_to_hm(seconds: int) -> tuple[int, int]:
    """
    :param seconds: Time limit in seconds
    :return: Time limit in hh, mm, ss
    """
    # note: int won't round, eg: int(0.9) = 0
    hour = int(seconds / 3600)
    minute = int(seconds / 60 - hour * 60)
    return hour, minute


def gen_airports(database, player, number):
    """
    Generate random airports and save to database
    :param number: The number of airports desired
    """
    airports = {}
    sql_query = """SELECT ident, airport.iso_country, airport.name, country.name as country_name, latitude_deg, longitude_deg
                    FROM airport
                    JOIN country on airport.iso_country = country.iso_country
                    WHERE airport.continent = 'EU'
                    AND type = 'large_airport'
                    ORDER BY RAND()
                    LIMIT %s"""
    response = database.query(sql_query, number)

    # save to dictionary
    home_set = False
    for airport in response:
        # wrap data in ident
        ident = airport["ident"]
        airports[ident] = airport

        # set home airport and current airport
        if not home_set:
            player.update_state(home=ident, location=ident)
            airport["visit"] = 1
            home_set = True
        else:
            airport["visit"] = 0

    # save to database
    for ident in airports.keys():
        airport = airports[ident]
        parameter = (player.game_id, airport["iso_country"], airport["country_name"], ident,
                     airport["name"], airport["latitude_deg"], airport["longitude_deg"], airport["visit"])

        sql_query = """INSERT INTO game_airport (game_id, iso_country, country_name, ident, name, 
                        latitude_deg, longitude_deg, visit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        database.query(sql_query, parameter)
    return airports


def second_to_dhm(seconds: int) -> tuple[int, int, int]:
    """
    :param seconds: Time limit in seconds
    :return: Time limit in hh, mm, ss
    """
    # note: int won't round, eg: int(0.9) = 0
    day = int(seconds / 3600 / 24)
    hour = int(seconds / 3600 - day * 24)
    minute = int(seconds / 60 - hour * 60 - day * 24 * 60)
    return day, hour, minute

