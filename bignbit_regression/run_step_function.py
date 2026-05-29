import boto3
import json
import argparse
import sys
import time


def start_step_function(sfn_client, state_machine_arn: str, input_data: dict) -> dict:
    """
    Start an AWS Step Function execution with JSON input.
    
    Args:
        sfn_client: Boto3 Step Functions client
        state_machine_arn: The ARN of the Step Function state machine
        input_data: Dictionary containing the input data for the execution
    
    Returns:
        Dictionary containing the execution response
    """
    response = sfn_client.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(input_data)
    )
    return response


def wait_for_execution(sfn_client, execution_arn: str, poll_interval: int = 10) -> dict:
    """
    Wait for a Step Function execution to complete.
    
    Args:
        sfn_client: Boto3 Step Functions client
        execution_arn: The ARN of the execution to monitor
        poll_interval: Seconds between status checks (default: 10)
    
    Returns:
        Dictionary containing the final execution description
    """
    print(f"\nMonitoring execution: {execution_arn}")
    print(f"Polling every {poll_interval} seconds...")
    
    running_statuses = ['RUNNING', 'PENDING_REDRIVE']
    
    while True:
        response = sfn_client.describe_execution(executionArn=execution_arn)
        status = response['status']
        
        print(f"  Status: {status}", end='')
        
        if status not in running_statuses:
            print()  # newline
            break
        
        print(f" - waiting {poll_interval}s...")
        time.sleep(poll_interval)
    
    return response


def run_step_function(
    state_machine_arn: str,
    input_file: str,
    region: str = "us-west-2",
    poll_interval: int = 10,
    no_wait: bool = False,
    aws_profile: str = None
):
    """
    Run a Step Function regression test.

    Args:
        state_machine_arn: ARN of the Step Function state machine
        input_file: JSON input file path or JSON string
        region: AWS region (default: us-west-2)
        poll_interval: Seconds between status checks (default: 10)
        no_wait: If True, start execution and return without waiting
        aws_profile: AWS profile name for credentials (default: None uses default)

    Returns:
        Dictionary containing the execution response
    """
    # Parse input data
    try:
        # Try to read as file first
        try:
            with open(input_file, 'r') as f:
                input_data = json.load(f)
        except FileNotFoundError:
            # If file not found, try parsing as JSON string
            input_data = json.loads(input_file)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        raise e
    
    # Create Step Functions client
    session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
    sfn_client = session.client('stepfunctions', region_name=region)
    
    # Start the Step Function execution
    try:
        start_response = start_step_function(
            sfn_client=sfn_client,
            state_machine_arn=state_machine_arn,
            input_data=input_data
        )
        
        execution_arn = start_response['executionArn']
        print(f"Step Function execution started successfully!")
        print(f"Execution ARN: {execution_arn}")
        print(f"Start Date: {start_response['startDate']}")
        
        if no_wait:
            return start_response
        
        # Wait for execution to complete
        final_response = wait_for_execution(
            sfn_client=sfn_client,
            execution_arn=execution_arn,
            poll_interval=poll_interval
        )
        
        status = final_response['status']
        print(f"\n{'='*60}")
        print(f"Execution completed with status: {status}")
        print(f"Stop Date: {final_response.get('stopDate', 'N/A')}")
        print(f"{'='*60}")
        
        # Output results based on status
        if status == 'SUCCEEDED':
            output = final_response.get('output')
            if output:
                print("\nOutput:")
                print(json.dumps(json.loads(output), indent=2))
            return final_response
        
        elif status == 'FAILED':
            print(f"\nError: {final_response.get('error', 'Unknown error')}")
            print(f"Cause: {final_response.get('cause', 'Unknown cause')}")
        
        elif status == 'TIMED_OUT':
            print("\nExecution timed out")
        
        elif status == 'ABORTED':
            print("\nExecution was aborted")
        
        else:
            print(f"\nUnexpected status: {status}")

        return final_response
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)



def main():
    parser = argparse.ArgumentParser(
        description='Start an AWS Step Function execution with JSON input and wait for completion'
    )
    parser.add_argument(
        '--state-machine-arn',
        required=True,
        help='ARN of the Step Function state machine'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='JSON input file path or JSON string'
    )
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=10,
        help='Seconds between status checks (default: 10)'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        help='Start execution and exit without waiting for completion'
    )
    
    args = parser.parse_args()
    
    run_step_function(
        state_machine_arn=args.state_machine_arn,
        input_file=args.input,
        region=args.region,
        poll_interval=args.poll_interval,
        no_wait=args.no_wait
    )

if __name__ == '__main__':
    main()
