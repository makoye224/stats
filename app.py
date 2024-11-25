import requests
import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask import Flask, render_template_string

# Initialize Flask app
app = Flask(__name__)

# Define your API endpoint
api_uri = 'https://q3j9h4ici8.execute-api.us-east-1.amazonaws.com/prod/courses/'

# Fetch data from the API
response = requests.get(api_uri)

# Check if the request was successful
if response.status_code == 200:
    courses_data = response.json()
    print("Data fetched successfully!")
else:
    print(f"Failed to fetch data: {response.status_code}")
    courses_data = []

# Normalize the data to extract reviews for each course
courses = []
for course in courses_data:
    for review in course.get('reviews', []):
        courses.append({
            'Course ID': course['courseId'],
            'Title': course['title'],
            'Overall Rating': review.get('overall', None),
            'Difficulty': review.get('difficulty', None),
            'Usefulness': review.get('usefulness', None),
            'Major': review.get('major', 'Unknown'),
            'Anonymous': review.get('anonymous', 'false'),
            'Additional Comments': review.get('additionalComments', None),
            'Tips': review.get('tips', None),
            'Professor': review.get('professor', 'Unknown'),
            'Date': review.get('createdAt', None)  # Assuming there's a createdAt field for the date
        })

# Create a DataFrame from the extracted data
df = pd.DataFrame(courses)

# Ensure the DataFrame is not empty
if df.empty:
    print("No data available for analysis.")
    exit()

# Function to categorize anonymity
def anongroup(author):
    # Ensure the value is a string before calling .lower()
    if isinstance(author, str):
        return 'true' if author.lower() == 'anon' else 'false'
    # Handle boolean True/False as 'true'/'false'
    elif isinstance(author, bool):
        return 'true' if author else 'false'
    # Fallback for unexpected types
    return 'false'

# Add 'Is Anonymous' column safely
if 'Anonymous' in df.columns:
    df['Is Anonymous'] = df['Anonymous'].apply(anongroup)
else:
    print("Warning: 'Anonymous' column not found.")
    df['Is Anonymous'] = 'false'

# Create visualizations using Plotly
pio.templates.default = "plotly_white"

fig1 = px.pie(df, names='Major', opacity=0.65, title="Breakdown of Majors")
fig2 = px.scatter(df, x='Overall Rating', y='Difficulty', opacity=0.65, 
                  title="Overall Rating vs Difficulty", 
                  hover_data=['Difficulty', 'Usefulness', 'Major'], 
                  trendline='ols', marginal_x='box', marginal_y='box')
fig3 = px.histogram(df, x='Overall Rating', facet_row='Is Anonymous', 
                    title="Overall Rating Distribution by Anonymity Status", 
                    color='Is Anonymous')
fig4 = px.scatter_3d(df, x='Overall Rating', y='Difficulty', z='Usefulness', 
                     title='Difficulty vs Usefulness vs Rating', color='Is Anonymous')
fig5 = px.scatter_matrix(df, dimensions=["Difficulty", "Overall Rating", "Usefulness"], 
                         color='Is Anonymous', title='Relationships Between Review Metrics')

# Generate HTML for the visualizations
plot1 = fig1.to_html(full_html=False)
plot2 = fig2.to_html(full_html=False)
plot3 = fig3.to_html(full_html=False)
plot4 = fig4.to_html(full_html=False)
plot5 = fig5.to_html(full_html=False)

# Flask route to render the visualizations
@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Course Review Analysis</title>
    </head>
    <body>
        <h1>Course Review Analysis</h1>
        <h3>A Look at Data from Course Review Posts</h3>
        <div>{{ plot1|safe }}</div>
        <div>{{ plot2|safe }}</div>
        <div>{{ plot3|safe }}</div>
        <div>{{ plot4|safe }}</div>
        <div>{{ plot5|safe }}</div>
    </body>
    </html>
    ''', plot1=plot1, plot2=plot2, plot3=plot3, plot4=plot4, plot5=plot5)

if __name__ == '__main__':
    app.run(debug=True)
