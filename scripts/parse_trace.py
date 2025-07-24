import csv

input_txt = 'trace.txt'
output_csv = 'trace.csv'

with open(input_txt, 'r') as infile, open(output_csv, 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(['frame_id', 'tipo', 'tamanho', 'seq_num', 'duracao'])
    for line in infile:
        parts = line.strip().split()
        if len(parts) == 5:
            writer.writerow(parts)

print(f"Arquivo {output_csv} gerado com sucesso.")
