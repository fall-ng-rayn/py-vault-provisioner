from app.services.load_project_inputs import load_all_inputs, summarize_scan

print("------------------------------------------------------------")
print("Running scan test")

scan = load_all_inputs()
print(summarize_scan(scan))
print("------------------------------------------------------------")
