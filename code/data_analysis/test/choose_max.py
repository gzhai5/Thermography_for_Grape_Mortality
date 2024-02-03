import pandas as pd

def process_csv(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file)

    # get the min value of rows for Label == True and Label == False
    true_count = len(df[df['Label'] == True])
    print('True count:', true_count)
    false_count = len(df[df['Label'] == False])
    print('False count:', false_count)
    min_count = min(true_count, false_count)
    print('Min count:', min_count)

    # Filter rows where Label is True and False
    true_rows = df[df['Label'] == True].sample(min_count)
    false_rows = df[df['Label'] == False].sample(min_count)

    # Combine the rows
    combined_rows = pd.concat([true_rows, false_rows])

    # Save to a new CSV file
    combined_rows.to_csv(output_file, index=False)

# Example usage
input_file = '../roi_data_pn_2.csv'
output_file = '../roi_data_pn_2_processed.csv'
process_csv(input_file, output_file)
