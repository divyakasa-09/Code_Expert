import snowflake.connector

try:
    conn = snowflake.connector.connect(
        user="divk",
        password="Chintu@18",
        account="tvebxnn.rmb14019.us-west-2.aws"
    )
    print("Snowflake connection successful!")
except Exception as e:
    print(f"Snowflake connection failed: {e}")
