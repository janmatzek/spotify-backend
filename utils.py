""" utilities module """

import json

from google.api_core import exceptions as api_exceptions
from google.auth import exceptions as auth_exceptions
from google.auth.exceptions import RefreshError
from google.cloud import bigquery
from google.oauth2 import service_account


def send_response(status_code, message, e=""):
    """
    Constructs and returns a response dictionary containing status code and message.

    Args:
        status_code (int): The HTTP status code to be included in the response.
        message (str): The main message to be included in the response.
        e (str, optional): Additional error information to be appended to the message.
            -> Defaults to "".

    Returns:
        dict: A dictionary containing the HTTP status code and the message as a JSON string.
    """
    if e == "":
        sep = ""
    else:
        sep = "\n"

    response = {"status_code": status_code, "body": json.dumps({"message": f"{message}{sep}{e}"})}

    print(response)
    return response


def parse_query_result(query_result):
    """
    Parses the result of a BigQuery query into a list of dictionaries.

    Args:
        query_result (google.cloud.bigquery.table.RowIterator): The result of a BigQuery query.

    Returns:
        list: A list of dictionaries, where each dictionary represents a row of the query result.
              The keys are column names, and the values are the corresponding values in the row.
    """

    rows = []
    for row in query_result:
        row_data = {}
        for key, value in row.items():
            # Convert any special types if needed (e.g., datetime)
            row_data[key] = value
        rows.append(row_data)
    return rows


def setup_big_query_client(project_id, service_account_path):
    """attempts to set up a BigQuery client"""
    try:
        big_query_client = bigquery.Client(
            project=project_id,
            credentials=service_account.Credentials.from_service_account_file(service_account_path),
        )
        status = send_response(200, "BigQuery client initiated")
    except auth_exceptions.DefaultCredentialsError as e:
        status = send_response(
            500, "Could not create BigQuery client - Default credentials error", e
        )
    except api_exceptions.GoogleAPIError as e:
        status = send_response(500, "Could not create BigQuery client - Google API error", e)
    except RefreshError as e:
        status = send_response(500, "Could not create BigQuery client - Token refresh error", e)
    except Exception as e:  # pylint: disable=broad-except
        status = send_response(500, "Could not create BigQuery client - Unknown error", e)

    return status, big_query_client


def run_query(big_query_client, str_query):
    """
    Executes a BigQuery query and returns the query result along with the status.

    Args:
        big_query_client (google.cloud.bigquery.client.Client): The BigQuery client instance.
        str_query (str): The SQL query string to be executed.

    Returns:
        tuple: A tuple containing the status of the query execution and the query result.
               - status (dict): A dictionary containing the HTTP status code and message
                    of the query execution.
               - query_result (google.cloud.bigquery.table.RowIterator):
                    The result of the query if successful, otherwise None.

    Notes:
        The status dictionary contains the following keys:
            - 'status_code' (int): The HTTP status code.
            - 'body' (str): The response message.

        The query_result is a RowIterator object representing the result of the query.
        If an error occurs during query execution, query_result will be None.
    """
    query_result = None  # Default value for query_result
    try:
        query_job = big_query_client.query(query=str_query)
        query_result = query_job.result()
        status = send_response(200, "Query successful")
    except api_exceptions.BadRequest as e:
        status = send_response(400, "Bad request: invalid query syntax", e)
    except api_exceptions.GoogleAPIError as e:
        status = send_response(500, "Google API error: unable to execute the query", e)
    except Exception as e:  # pylint: disable=broad-except
        status = send_response(500, "Unknown error occurred while executing the query", e)

    return status, query_result
