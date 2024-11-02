from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def execute_graphql_query(concept_id, env, headers):

    if env == 'uat':
        url = "https://graphql.uat.earthdata.nasa.gov/api"
    else:
        url = "https://graphql.earthdata.nasa.gov/api"

    # Select your transport with a defined url endpoint
    transport = RequestsHTTPTransport(url=url, headers=headers, retries=10, retry_backoff_factor=0.5)

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Provide a GraphQL query
    query = gql(
        """
        query MyQuery {
            collections(params: {conceptId: "%s"}) {
                items {
                    shortName
                    conceptId
                    granules(params: { limit: 1, sortKey: ["-start_date"] }) {
                        count
                        items {
                            conceptId
                            spatialExtent
                            temporalExtent
                            relatedUrls
                        }
                    }
                    variables {
                        items {
                            conceptId
                            name
                            variableType
                            variableSubType
                        }
                    }
                }
            }
        }
    """ % concept_id
    )

    # Execute the query on the transport
    return client.execute(query)
