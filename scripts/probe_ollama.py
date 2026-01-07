import os, asyncio, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.providers.ollama import OllamaProvider
from backend.providers.types import ProviderRequest

async def main():
    host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    p = OllamaProvider(host)
    req = ProviderRequest(model='llama3.2:latest', messages=[{'role':'user','content':'hi'}], metadata={})
    resp = await p.chat(req)
    print('ok', resp.ok, 'len', len(resp.content or ''), 'meta', resp.provider_meta, 'err', getattr(resp, 'error', None))

if __name__ == '__main__':
    asyncio.run(main())
