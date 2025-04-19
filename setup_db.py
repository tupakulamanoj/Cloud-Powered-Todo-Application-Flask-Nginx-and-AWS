import pymysql
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Manoj2025')  # Replace with your actual password or use .env file
DB_NAME = os.environ.get('DB_NAME', 'flask_todo')

def execute_sql_file(filename):
    """
    Execute SQL statements from a file
    """
    # Read SQL file
    with open(filename, 'r') as f:
        sql_script = f.read()
    
    # Split the script into individual statements
    # This simple split works for most basic SQL files
    # For more complex SQL with stored procedures etc., you might need a more sophisticated parser
    statements = sql_script.split(';')
    
    # Connect to MySQL server (without specifying database, as it may not exist yet)
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"Connected to MySQL server at {DB_HOST}")
        
        try:
            with connection.cursor() as cursor:
                # Execute each statement
                for statement in statements:
                    # Skip empty statements
                    if statement.strip():
                        print(f"Executing: {statement.strip()[:60]}...")
                        cursor.execute(statement)
                
                connection.commit()
                print("SQL script executed successfully!")
                
        except Exception as e:
            print(f"Error executing SQL: {e}")
            
    except pymysql.err.OperationalError as e:
        print(f"Error connecting to MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("MySQL connection closed")

def check_database_tables():
    """
    Check if database and tables exist
    """
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,  # Now connecting to the specific database
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        try:
            with connection.cursor() as cursor:
                # Check tables
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"Database '{DB_NAME}' contains these tables:")
                for table in tables:
                    table_name = list(table.values())[0]
                    print(f"- {table_name}")
                    
                    # Show table structure
                    cursor.execute(f"DESCRIBE {table_name}")
                    columns = cursor.fetchall()
                    for column in columns:
                        print(f"  - {column['Field']} ({column['Type']})")
                
        except Exception as e:
            print(f"Error checking tables: {e}")
            
    except pymysql.err.OperationalError as e:
        print(f"Error connecting to database {DB_NAME}: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    # Execute the SQL file
    execute_sql_file("schema.sql")
    
    # Check if database and tables were created
    check_database_tables()