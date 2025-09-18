import csv


def write_result_to_csv(result, csv_path, csv_filename):
    """Write a single result to CSV file"""
    file_exists = csv_path.exists()

    with open(csv_filename, "a", newline="", encoding="utf-8") as csvfile:
        if isinstance(result, dict):
            fieldnames = result.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header only if file is new
            if not file_exists:
                writer.writeheader()

            writer.writerow(result)
        else:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["result"])  # Header
            writer.writerow([result])
