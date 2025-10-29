import duckdb
from datetime import datetime
from pathlib import Path

def validate_data(con, table_name: str) -> bool:
    """Validates if the data meets the required format"""
    try:
        #Check schema
        columns = con.query(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'").fetchall()
        column_names = {col[0] for col in columns}
        required_columns = {'id', 'name', 'country', 'is_botafoguense'}
        
        if not required_columns.issubset(column_names):
            print("Missing required columns")
            return False
        
        #Check for null values 
        null_check = con.query(f"""
            SELECT COUNT(*) 
            FROM {table_name} 
            WHERE id IS NULL 
               OR name IS NULL 
               OR country IS NULL 
               OR is_botafoguense IS NULL
        """).fetchone()[0]
        
        if null_check > 0:
            print("Null values found")
            return False
        
        #Check is_botafoguense values
        valid_check = con.query(f"""
            SELECT COUNT(*) 
            FROM {table_name} 
            WHERE is_botafoguense NOT IN (0, 1)
        """).fetchone()[0]
        
        if valid_check > 0:
            print("Invalid values in is_botafoguense column")
            return False
        
        return True
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return False

def process_file(input_file: str, output_file: str) -> bool:
    """Process a CSV file applying the necessary transformations"""
    con = None
    try:
        # Create in-memory DuckDB connection
        con = duckdb.connect(database=':memory:')
        
        con.sql(f"""
            CREATE TABLE input_data AS 
            SELECT * FROM read_csv_auto('{input_file}')
        """)
        
        if not validate_data(con, 'input_data'):
            print(f"Data validation failed: {input_file}")
            return False
        
        con.sql(f"""
            CREATE TABLE output_data AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY name) as id,
                name,
                country,
                is_botafoguense,
                '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}' as last_update_date
            FROM input_data
            ORDER BY name
        """)
        
        con.sql(f"""
            COPY output_data TO '{output_file}' (HEADER, DELIMITER ',')
        """)
        
        print(f"File processed successfully: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")
        return False
    finally:
        if con:
            con.close()

if __name__ == "__main__":
    # Setup paths
    input_dir = Path('input')
    output_dir = Path('output')

    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # List of files to process
    files_to_process = [
        ('palestrantes.csv', 'palestrantes_processed.csv')
    ]
    
    # Process each file
    for input_file, output_file in files_to_process:
        input_path = input_dir / input_file
        output_path = output_dir / output_file
        
        if process_file(str(input_path), str(output_path)):
            print(f"✓ {input_file} processed successfully")
        else:
            print(f"✗ Error processing {input_file}")