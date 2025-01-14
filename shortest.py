import pandas as pd
import requests
import googlemaps
import folium


class ShortestDist():
    def __init__(self, address):
        self.address = address
        self.df = pd.read_csv("Licensed_Establishment.csv")
        self.df = self.df[self.df["EstablishmentType"].str.contains("Food")][["DoingBusinessAsName", "AddressFull"]].reset_index(drop=True)
        
        def zipCode(x):
            return int(x.split(" ")[-1].split("-")[0])

        self.df["ZIPCODE"] = self.df["AddressFull"].apply(zipCode)
        self.df = self.df[((self.df['ZIPCODE']>53703) & (self.df['ZIPCODE'] < 53715))].reset_index(drop=True)
        self.api = 'INSERT GOOGLE API'
        self.gmaps = googlemaps.Client(key=self.api)
        self.destination = None
        self.duration = 0
        self.distance = 0
        self.name = None
        

    def geoCoordGen(self, address):
        geocode_result = self.gmaps.geocode(address)

        latitude = geocode_result[0]["geometry"]["location"]["lat"]
        longitude = geocode_result[0]["geometry"]["location"]["lng"]

        return latitude, longitude
    
    def get_distance_matrix(self, origin, destination):
        """Calculate distance and time between two coordinates using Google Maps Distance Matrix API."""

        url = "https://maps.googleapis.com/maps/api/distancematrix/json"

        params = {
            "units": "imperial",
            "origins": f"{origin[0]},{origin[1]}",
            "destinations": f"{destination[0]},{destination[1]}",
            "key": self.api
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return "Error: The API request was unsuccessful."
        
    def getInfoDistance(self, address, destination):
        result = self.get_distance_matrix(self.geoCoordGen(address), self.geoCoordGen(destination))  # Debugging: Print the response
        
        if 'rows' in result and result['rows']:
            elements = result['rows'][0].get('elements', [])
            if elements and elements[0].get('status') == 'OK':
                distance_text = elements[0]['distance']['text']
                duration_text = elements[0]['duration']['text']
                return float(distance_text.split(" ")[0]), int(duration_text.split(" ")[0])
        return 0, 0  # Default values if API response is invalid
            

    def getShortest(self): 
        # Calculate distance and duration for each row
        self.df[['Distance', 'Duration']] = self.df.apply(
            lambda row: self.getInfoDistance(self.address, row['AddressFull']), 
            axis=1, 
            result_type='expand'
        )

        # Sort DataFrame by 'Duration' and reset index
        self.df = self.df.sort_values(by='Duration', ascending=True).reset_index(drop=True)

        # Select the top 3 rows with the smallest duration
        top3_rows = self.df.head(3)

        # Iterate over each of the top 3 rows to store their information
        self.destinations = top3_rows["AddressFull"].tolist()
        self.durations = top3_rows["Duration"].tolist()
        self.distances = top3_rows["Distance"].tolist()
        self.names = top3_rows["DoingBusinessAsName"].tolist()

    def getCoord(self):
        print("Started Calculating Shortest Distance")
        self.getShortest()
        print("Finished Calculating!")
        output_dicts = []

        for i in range(len(self.destinations)):
            output_dict = {
                "Origin Coordinates": [self.geoCoordGen(self.address)],
                "Destination Coordinates": [self.geoCoordGen(self.destinations[i])],
                "Origin Address": self.address,
                "Destination Address": self.destinations[i],
                "Duration(min)": self.durations[i],
                "Distance(miles)": self.distances[i],
                "Name": self.names[i]
            }
            output_dicts.append(output_dict)

        # Create a map centered around a specific location (e.g., Madison, Wisconsin)
        madison_coords = [43.0731, -89.4012]
        map_madison = folium.Map(location=madison_coords, zoom_start=12)

        # Add markers for the origin and all destinations to the map
        folium.Marker(
            location=output_dicts[0]['Origin Coordinates'][0], 
            popup='Origin', 
            icon=folium.Icon(color='red')
        ).add_to(map_madison)

        for output_dict in output_dicts:
            folium.Marker(
                location=output_dict['Destination Coordinates'][0], 
                popup=f"Destination: {output_dict['Name']}", 
                icon=folium.Icon(color='blue')
            ).add_to(map_madison)

        # Display the map
        map_madison.save('static/madison_map.html')
        
        return pd.DataFrame(output_dicts)

        

        

