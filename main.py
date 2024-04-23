from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv
from utils import *
import os
import json
load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:3000",
]

# Add CORS middleware to your FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/scorecards/{period}")
async def fetch_scorecards_data(period: str):
    if period == 'last_24':
        queried_table = os.getenv("TABLE_ID_24")
    elif period == "all_time":
        queried_table = os.getenv("TABLE_ID_FULL")
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    str_query = f"""
        SELECT 
            COUNT(track_id) AS count_tracks,
            COUNT(DISTINCT(track_id)) AS distinct_tracks,
            COUNT(DISTINCT(track_artists_id)) AS count_artists,
            SUM(track_duration_ms) as total_duration_ms,
            AVG(track_popularity) as avg_popularity
        from {queried_table}
    """

    try:
        big_query_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"), credentials=service_account.Credentials.from_service_account_file(os.getenv("SERVICE_ACCOUNT_PATH")))
    except Exception as e:
        send_response(500, "Could not create BigQuery client", e)

    try:
        query_job = big_query_client.query(query = str_query)
        query_result = query_job.result()
    except Exception as e:
        send_response(500, "Unable to execute the query", e)

    data = parse_query_result(query_result)

    return Response(content=json.dumps(data[0]), status_code=200)


@app.get("/bars/{period}")
async def fetch_bars_data(period: str):
    if period == 'last_24':
        queried_table = os.getenv("TABLE_ID_24")
        str_query = f"""
            WITH hours AS (
                SELECT 
                    DATETIME(DATETIME_SUB(CURRENT_DATETIME('UTC'), INTERVAL offset HOUR)) AS date_played_at,
                    EXTRACT(HOUR FROM CURRENT_DATETIME('UTC') - INTERVAL offset HOUR) AS hour_played_at
                FROM UNNEST(GENERATE_ARRAY(1, 24)) AS offset
            )

            SELECT 
                hours.date_played_at,
                hours.hour_played_at,
                COUNT(data.track_id) AS track_count
            FROM 
                hours
            LEFT JOIN 
                `{queried_table}` AS data
            ON 
                DATE(data.played_at) = DATE(hours.date_played_at)
                AND EXTRACT(HOUR FROM data.played_at) = hours.hour_played_at
            GROUP BY 
                hours.date_played_at, hours.hour_played_at
            ORDER BY 
                hours.date_played_at, hours.hour_played_at

        """
    elif period == "all_time":
        queried_table = os.getenv("TABLE_ID_FULL")
        str_query = """""" # ! add the query
    else:
        raise HTTPException(status_code=400, detail="Invalid period")

    try:
        big_query_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"), credentials=service_account.Credentials.from_service_account_file(os.getenv("SERVICE_ACCOUNT_PATH")))
    except Exception as e:
        send_response(500, "Could not create BigQuery client", e)

    try:
        query_job = big_query_client.query(query = str_query)
        query_result = query_job.result()
    except Exception as e:
        send_response(500, "Unable to execute the query", e)

    data = parse_query_result(query_result)
    
    processed_data = [{"hour": item["hour_played_at"], "count": item["track_count"]} for item in data]

    return Response(content=json.dumps(processed_data), status_code=200)

# left doughnut chart 
@app.get("/pie_context/{period}")
async def fetch_context_pie_data(period: str):
    if period == 'last_24':
        queried_table = os.getenv("TABLE_ID_24")
    elif period == "all_time":
        queried_table = os.getenv("TABLE_ID_FULL")
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    str_query = f"""
        SELECT
            context_type AS category, count(track_id) AS value
        FROM
            {queried_table}
        GROUP BY
            context_type
    """

    try:
        big_query_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"), credentials=service_account.Credentials.from_service_account_file(os.getenv("SERVICE_ACCOUNT_PATH")))
    except Exception as e:
        send_response(500, "Could not create BigQuery client", e)

    try:
        query_job = big_query_client.query(query = str_query)
        query_result = query_job.result()
    except Exception as e:
        send_response(500, "Unable to execute the query", e)

    data = parse_query_result(query_result)

    return Response(content=json.dumps(data), status_code=200)

# middle doughnut chart
@app.get("/pie_artists/{period}")
async def fetch_artists_pie_data(period: str):
    if period == 'last_24':
        queried_table = os.getenv("TABLE_ID_24")
    elif period == "all_time":
        queried_table = os.getenv("TABLE_ID_FULL")
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    str_query = f"""
        SELECT
            STRING_AGG(DISTINCT track_artists_name) as category,
            COUNT(track_id) as value
        FROM
            {queried_table}
        GROUP BY
            track_artists_id
    """

    try:
        big_query_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"), credentials=service_account.Credentials.from_service_account_file(os.getenv("SERVICE_ACCOUNT_PATH")))
    except Exception as e:
        send_response(500, "Could not create BigQuery client", e)

    try:
        query_job = big_query_client.query(query = str_query)
        query_result = query_job.result()
    except Exception as e:
        send_response(500, "Unable to execute the query", e)

    data = parse_query_result(query_result)

    return Response(content=json.dumps(data), status_code=200)

# right doughnut chart
@app.get("/pie_release_years/{period}")
async def fetch_release_pie_data(period: str):
    if period == 'last_24':
        queried_table = os.getenv("TABLE_ID_24")
    elif period == "all_time":
        queried_table = os.getenv("TABLE_ID_FULL")
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    str_query = f"""
        SELECT
            SPLIT(track_album_release_date, '-')[OFFSET(0)] AS category,
            COUNT(track_id) AS value
        FROM
            {queried_table}
        GROUP BY
            category
    """

    try:
        big_query_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"), credentials=service_account.Credentials.from_service_account_file(os.getenv("SERVICE_ACCOUNT_PATH")))
    except Exception as e:
        send_response(500, "Could not create BigQuery client", e)

    try:
        query_job = big_query_client.query(query = str_query)
        query_result = query_job.result()
    except Exception as e:
        send_response(500, "Unable to execute the query", e)

    data = parse_query_result(query_result)

    return Response(content=json.dumps(data), status_code=200)

# the data table
@app.get("/table/{period}")
async def fetch_table_data(period: str):
    if period == 'last_24':
        queried_table = os.getenv("TABLE_ID_24")
    elif period == "all_time":
        queried_table = os.getenv("TABLE_ID_FULL")
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    str_query = f"""
        SELECT
            STRING_AGG(DISTINCT track_album_images_url) AS album_image_url,
            STRING_AGG(DISTINCT track_name) AS track_name,
            STRING_AGG(DISTINCT track_album_name) AS album_name,
            STRING_AGG(DISTINCT track_artists_name) AS artist_name,
            CONCAT('https://open.spotify.com/track/',track_id) AS track_url,
        FROM
            {queried_table}
        GROUP BY
            track_id
        ORDER BY
            COUNT(track_id) DESC,
            AVG(track_popularity) ASC
        LIMIT
            5

    """

    try:
        big_query_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"), credentials=service_account.Credentials.from_service_account_file(os.getenv("SERVICE_ACCOUNT_PATH")))
    except Exception as e:
        send_response(500, "Could not create BigQuery client", e)

    try:
        query_job = big_query_client.query(query = str_query)
        query_result = query_job.result()
    except Exception as e:
        send_response(500, "Unable to execute the query", e)

    data = parse_query_result(query_result)

    return Response(content=json.dumps(data), status_code=200)