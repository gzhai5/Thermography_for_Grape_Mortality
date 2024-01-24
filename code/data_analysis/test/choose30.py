import pandas as pd

def process_csv(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file)

    # Filter rows where Label is True and False
    true_rows = df[df['Label'] == True].sample(30)
    false_rows = df[df['Label'] == False].sample(30)

    # Combine the rows
    combined_rows = pd.concat([true_rows, false_rows])

    # Save to a new CSV file
    combined_rows.to_csv(output_file, index=False)

# Example usage
input_file = '../roi_data.csv'
output_file = '../roi_data_30.csv'
process_csv(input_file, output_file)
