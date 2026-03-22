import argparse

from audit_app.services.audit_service import process_audit_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--empresa", required=True)
    parser.add_argument("-f", "--fecha", required=True)
    parser.add_argument("-i", "--input", default="input.csv")
    args = parser.parse_args()

    result, error = process_audit_data(args.empresa, args.fecha, input_filename=args.input)
    if error:
        print(error)
        raise SystemExit(1)

    print(f"Reporte generado: {result['output_xlsx']}")
