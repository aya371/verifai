code = open('claim_extractor.py', encoding='utf-8').read()
open('backend/agents/claim_extractor.py', 'w', encoding='utf-8').write(code)
print('claim_extractor.py updated successfully!')
print('Now run: python run_demo.py')
