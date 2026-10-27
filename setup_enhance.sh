# One-time setup per session for enhance_vo.py (Resemble Enhance, CPU). Takes ~3 min, ~1.5 GB.
# GitHub downloads are blocked here, so weights come from Hugging Face; deepspeed (training only) is stubbed.
set -e
V=/home/claude/dfenv
python3 -m venv $V
$V/bin/pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu
$V/bin/pip install -q --no-deps resemble-enhance
$V/bin/pip install -q librosa omegaconf resampy tabulate rich celluloid scipy matplotlib pandas tqdm
SP=$($V/bin/python -c "import site;print(site.getsitepackages()[0])")
mkdir -p $SP/deepspeed/runtime
printf 'class DeepSpeedConfig: pass\ndef init_distributed(*a, **k): pass\n' > $SP/deepspeed/__init__.py
printf "class _A:\n    def device_name(self,*a): return 'cpu'\ndef get_accelerator(): return _A()\n" > $SP/deepspeed/accelerator.py
: > $SP/deepspeed/runtime/__init__.py
printf 'def clip_grad_norm_(*a,**k): pass\n' > $SP/deepspeed/runtime/utils.py
printf 'class DeepSpeedEngine: pass\n' > $SP/deepspeed/runtime/engine.py
# scipy fix (fsolve returns an array) and smaller chunks so 8 GB RAM is enough
sed -i 's/x0=0))/x0=0)[0])/' $SP/resemble_enhance/enhancer/lcfm/cfm.py
sed -i 's/chunk_seconds: float = 30.0/chunk_seconds: float = 8.0/' $SP/resemble_enhance/inference.py
M=/home/claude/re_model/enhancer_stage2; mkdir -p $M/ds/G/default
H=https://huggingface.co/ResembleAI/resemble-enhance/resolve/main/enhancer_stage2
curl -sSL -o $M/hparams.yaml $H/hparams.yaml
curl -sSL -o $M/ds/G/latest $H/ds/G/latest
curl -sSL -o $M/ds/G/default/mp_rank_00_model_states.pt $H/ds/G/default/mp_rank_00_model_states.pt
echo "enhance setup ok"