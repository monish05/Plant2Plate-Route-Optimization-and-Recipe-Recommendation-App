from flask import Flask, render_template, request
import pandas as pd
import recipes
import googleform
import shortest as s
import folium

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    schedule_num = request.args.get('schedule_num')
    # Call the get_schedule method passing user input
    # TODO: Replace 'fetch_schedule' with your method name and uncomment the import
    schedule_num= int(schedule_num)
    schedule = googleform.ExcelConversation(schedule_num).getFreeTimes()
    schedule.to_csv("saved_rn.csv", index=False)
    df =recipes.RecipeHandler().main()
    # Assume schedule_data is a DataFrame
    #schedule_data= pd.read_csv('recipeRec.csv')  # Dummy data for demonstration
    return render_template('schedule.html', data=df.to_dict('records'))

@app.route('/schedule.html')
def rms():
    # Render schedule.html with dummy data for demonstration
    # Dummy data for demonstration
    df= recipes.RecipeHandler().main()
    return render_template('schedule.html', data=df.to_dict('records'))

@app.route('/quickestroute.html')
def qr():
    return render_template('shortestpath.html')

    #INPUT: s.ShortestDist()
@app.route('/displayf.html', methods=['GET', 'POST'])
def map1():
    address = request.args.get('storedText')
    # print(address)
    xcoord=s.ShortestDist(address).getCoord()
    coord_data = xcoord.to_dict('records')
    # #shortest some function 
    # #TODO  return an html with a folium map in the same style as the above given html
    # #map_html = folium_map._repr_html_()
    return render_template('map_display.html', map_file="map_html.html", coord_data=coord_data)
    return "Hello"
    
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
