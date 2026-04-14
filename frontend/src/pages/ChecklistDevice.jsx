import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Loader2, Mic, QrCode, Smartphone, Volume2, Camera, CheckCircle2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { checklist as checklistApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const TOUCH_CELL_COUNT = 20;

function StatusButtons({ value, onChange }) {
  const options = [
    { key: "ok", label: "OK" },
    { key: "falha", label: "Falha" },
    { key: "nao_testado", label: "Nao testado" },
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <Button
          key={option.key}
          type="button"
          variant={value === option.key ? "default" : "outline"}
          onClick={() => onChange(option.key)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  );
}

function statusLabel(status) {
  if (status === "ok") return "OK";
  if (status === "falha") return "Falha";
  return "Nao testado";
}

export default function ChecklistDevice() {
  const { token } = useParams();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [ordem, setOrdem] = useState(null);
  const [existingChecklist, setExistingChecklist] = useState(null);
  const [executadoPor, setExecutadoPor] = useState("");
  const [observacoes, setObservacoes] = useState("");
  const [touchMap, setTouchMap] = useState(() => Array.from({ length: TOUCH_CELL_COUNT }, () => false));
  const [draggingTouch, setDraggingTouch] = useState(false);
  const [testStatus, setTestStatus] = useState({
    touch: "nao_testado",
    audio: "nao_testado",
    microfone: "nao_testado",
    camera: "nao_testado",
    botoes: "nao_testado",
  });
  const [audioPlayed, setAudioPlayed] = useState(false);
  const [micState, setMicState] = useState({ supported: true, recording: false, previewUrl: "", error: "" });
  const [cameraState, setCameraState] = useState({ supported: true, active: false, error: "" });
  const [buttonChecks, setButtonChecks] = useState({ power: false, volumeUp: false, volumeDown: false, silent: false });
  const audioContextRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const cameraStreamRef = useRef(null);
  const cameraVideoRef = useRef(null);

  useEffect(() => {
    checklistApi.getPublic(token).then((res) => {
      if (!res?.ok) {
        toast.error(res?.erro || "Nao foi possivel carregar o checklist");
        setLoading(false);
        return;
      }

      const checklist = res.checklist || {};
      const savedTests = checklist.resultado?.testes || {};
      setOrdem(res.ordem || null);
      setExistingChecklist(checklist);
      setExecutadoPor(checklist.executado_por || "");
      setObservacoes(checklist.observacoes || "");
      setTestStatus({
        touch: checklist.status_touch || "nao_testado",
        audio: checklist.status_audio || "nao_testado",
        microfone: checklist.status_microfone || "nao_testado",
        camera: checklist.status_camera || "nao_testado",
        botoes: checklist.status_botoes || "nao_testado",
      });

      if (Array.isArray(savedTests.touch?.cells) && savedTests.touch.cells.length === TOUCH_CELL_COUNT) {
        setTouchMap(savedTests.touch.cells.map(Boolean));
      }
      if (savedTests.audio?.played) {
        setAudioPlayed(true);
      }
      if (savedTests.botoes?.checks) {
        setButtonChecks({
          power: Boolean(savedTests.botoes.checks.power),
          volumeUp: Boolean(savedTests.botoes.checks.volumeUp),
          volumeDown: Boolean(savedTests.botoes.checks.volumeDown),
          silent: Boolean(savedTests.botoes.checks.silent),
        });
      }
      setLoading(false);
    }).catch(() => {
      toast.error("Nao foi possivel carregar o checklist");
      setLoading(false);
    });

    return () => {
      if (cameraStreamRef.current) {
        cameraStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, [token]);

  useEffect(() => {
    const finishDrag = () => setDraggingTouch(false);
    window.addEventListener("pointerup", finishDrag);
    return () => window.removeEventListener("pointerup", finishDrag);
  }, []);

  const touchCoverage = useMemo(() => {
    const touched = touchMap.filter(Boolean).length;
    return Math.round((touched / TOUCH_CELL_COUNT) * 100);
  }, [touchMap]);

  const suggestedTouchStatus = useMemo(() => {
    if (touchCoverage >= 90) return "ok";
    if (touchCoverage > 0) return "falha";
    return "nao_testado";
  }, [touchCoverage]);

  const suggestedButtonsStatus = useMemo(() => {
    const values = Object.values(buttonChecks);
    if (values.every(Boolean)) return "ok";
    if (values.some(Boolean)) return "falha";
    return "nao_testado";
  }, [buttonChecks]);

  const markTouchCell = (index) => {
    setTouchMap((current) => current.map((cell, i) => (i === index ? true : cell)));
  };

  const handleTouchPointer = (event) => {
    const index = Number(event.currentTarget.dataset.cellIndex);
    if (Number.isInteger(index)) {
      markTouchCell(index);
    }
  };

  const playAudioTest = async () => {
    try {
      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextCtor) {
        toast.error("Seu navegador nao suporta audio programatico");
        return;
      }

      if (!audioContextRef.current || audioContextRef.current.state === "closed") {
        audioContextRef.current = new AudioContextCtor();
      }

      const ctx = audioContextRef.current;
      await ctx.resume();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(440, ctx.currentTime);
      oscillator.frequency.linearRampToValueAtTime(660, ctx.currentTime + 0.8);
      gainNode.gain.setValueAtTime(0.001, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.12, ctx.currentTime + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      oscillator.start();
      oscillator.stop(ctx.currentTime + 1.25);
      setAudioPlayed(true);
      toast.success("Som reproduzido");
    } catch {
      toast.error("Nao foi possivel reproduzir o som");
    }
  };

  const startMicTest = async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        setMicState((current) => ({ ...current, supported: false, error: "Microfone nao suportado neste navegador." }));
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const previewUrl = URL.createObjectURL(blob);
        setMicState({ supported: true, recording: false, previewUrl, error: "" });
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setMicState((current) => ({ ...current, supported: true, recording: true, error: "" }));
    } catch {
      setMicState((current) => ({ ...current, recording: false, error: "Permissao negada ou microfone indisponivel." }));
    }
  };

  const stopMicTest = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  };

  const startCameraTest = async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraState({ supported: false, active: false, error: "Camera nao suportada neste navegador." });
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      cameraStreamRef.current = stream;
      if (cameraVideoRef.current) {
        cameraVideoRef.current.srcObject = stream;
      }
      setCameraState({ supported: true, active: true, error: "" });
    } catch {
      setCameraState({ supported: true, active: false, error: "Nao foi possivel acessar a camera." });
    }
  };

  const stopCameraTest = () => {
    if (cameraStreamRef.current) {
      cameraStreamRef.current.getTracks().forEach((track) => track.stop());
      cameraStreamRef.current = null;
    }
    if (cameraVideoRef.current) {
      cameraVideoRef.current.srcObject = null;
    }
    setCameraState((current) => ({ ...current, active: false }));
  };

  const saveChecklist = async () => {
    setSaving(true);
    try {
      const payload = {
        executado_por: executadoPor,
        observacoes,
        origem: "qr_publico",
        testes: {
          touch: {
            status: testStatus.touch === "nao_testado" ? suggestedTouchStatus : testStatus.touch,
            cobertura_percentual: touchCoverage,
            cells: touchMap,
          },
          audio: {
            status: testStatus.audio,
            played: audioPlayed,
          },
          microfone: {
            status: testStatus.microfone,
            gravacao_disponivel: Boolean(micState.previewUrl),
          },
          camera: {
            status: testStatus.camera,
            visualizacao_ativa: cameraState.active,
          },
          botoes: {
            status: testStatus.botoes === "nao_testado" ? suggestedButtonsStatus : testStatus.botoes,
            checks: buttonChecks,
          },
        },
      };

      const res = await checklistApi.savePublic(token, payload);
      if (!res?.ok) {
        toast.error(res?.erro || "Nao foi possivel salvar o checklist");
        return;
      }
      setExistingChecklist(res.checklist || null);
      setTestStatus({
        touch: res.checklist?.status_touch || payload.testes.touch.status,
        audio: res.checklist?.status_audio || payload.testes.audio.status,
        microfone: res.checklist?.status_microfone || payload.testes.microfone.status,
        camera: res.checklist?.status_camera || payload.testes.camera.status,
        botoes: res.checklist?.status_botoes || payload.testes.botoes.status,
      });
      toast.success("Checklist salvo com sucesso");
    } catch {
      toast.error("Nao foi possivel salvar o checklist");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!ordem) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white px-6 text-center">
        <div className="max-w-md space-y-3">
          <AlertTriangle className="h-10 w-10 mx-auto text-amber-400" />
          <h1 className="text-2xl font-semibold">Checklist indisponivel</h1>
          <p className="text-slate-300">O link informado nao encontrou um aparelho valido para teste.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_#1e293b,_#020617_62%)] text-white">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <section className="rounded-3xl border border-white/10 bg-white/8 backdrop-blur-md p-5 space-y-4 shadow-2xl">
          <div className="flex items-start gap-3">
            <div className="rounded-2xl bg-cyan-400/15 p-3">
              <Smartphone className="h-6 w-6 text-cyan-300" />
            </div>
            <div className="space-y-1">
              <p className="text-xs uppercase tracking-[0.24em] text-cyan-200/80">Checklist de entrada</p>
              <h1 className="text-2xl font-semibold">OS #{ordem.id}</h1>
              <p className="text-sm text-slate-300">{ordem.cliente} • {ordem.modelo || "Modelo nao informado"}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-3">
              <p className="text-slate-400">Cor</p>
              <p className="font-medium">{ordem.cor || "Nao informada"}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-3">
              <p className="text-slate-400">IMEI</p>
              <p className="font-medium">{ordem.imei || "Nao informado"}</p>
            </div>
          </div>

          {existingChecklist?.atualizado_em ? (
            <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-100">
              Ultimo checklist salvo em {existingChecklist.atualizado_em}.
            </div>
          ) : null}
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/8 backdrop-blur-md p-5 space-y-4">
          <div className="flex items-center gap-3">
            <QrCode className="h-5 w-5 text-cyan-300" />
            <h2 className="text-lg font-semibold">Identificacao</h2>
          </div>
          <div className="space-y-2">
            <Label htmlFor="executado-por" className="text-slate-200">Quem executou o checklist</Label>
            <Input
              id="executado-por"
              value={executadoPor}
              onChange={(event) => setExecutadoPor(event.target.value)}
              placeholder="Nome do tecnico ou cliente"
              className="bg-slate-950/50 border-white/10 text-white"
            />
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/8 backdrop-blur-md p-5 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Touch</h2>
              <p className="text-sm text-slate-300">Passe o dedo por toda a grade. Cobertura atual: {touchCoverage}%.</p>
            </div>
            <CheckCircle2 className="h-5 w-5 text-cyan-300" />
          </div>
          <div className="grid grid-cols-4 gap-2">
            {touchMap.map((touched, index) => (
              <button
                key={index}
                type="button"
                data-cell-index={index}
                onPointerDown={(event) => {
                  setDraggingTouch(true);
                  handleTouchPointer(event);
                }}
                onPointerEnter={(event) => {
                  if (draggingTouch) handleTouchPointer(event);
                }}
                className={`aspect-square rounded-xl border transition ${touched ? "bg-cyan-400 border-cyan-200" : "bg-slate-950/50 border-white/10"}`}
              />
            ))}
          </div>
          <StatusButtons value={testStatus.touch} onChange={(value) => setTestStatus((current) => ({ ...current, touch: value }))} />
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/8 backdrop-blur-md p-5 space-y-4">
          <div className="flex items-center gap-3">
            <Volume2 className="h-5 w-5 text-cyan-300" />
            <div>
              <h2 className="text-lg font-semibold">Alto-falante</h2>
              <p className="text-sm text-slate-300">Reproduza o som e confirme se ele sai limpo.</p>
            </div>
          </div>
          <Button type="button" onClick={playAudioTest}>Reproduzir som de teste</Button>
          <p className="text-sm text-slate-400">Som reproduzido: {audioPlayed ? "sim" : "nao"}</p>
          <StatusButtons value={testStatus.audio} onChange={(value) => setTestStatus((current) => ({ ...current, audio: value }))} />
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/8 backdrop-blur-md p-5 space-y-4">
          <div className="flex items-center gap-3">
            <Mic className="h-5 w-5 text-cyan-300" />
            <div>
              <h2 className="text-lg font-semibold">Microfone</h2>
              <p className="text-sm text-slate-300">Grave um trecho curto e escute a reproducao.</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={startMicTest} disabled={micState.recording}>Iniciar gravacao</Button>
            <Button type="button" variant="outline" onClick={stopMicTest} disabled={!micState.recording}>Parar gravacao</Button>
          </div>
          {micState.error ? <p className="text-sm text-amber-300">{micState.error}</p> : null}
          {micState.previewUrl ? <audio controls src={micState.previewUrl} className="w-full" /> : null}
          <StatusButtons value={testStatus.microfone} onChange={(value) => setTestStatus((current) => ({ ...current, microfone: value }))} />
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/8 backdrop-blur-md p-5 space-y-4">
          <div className="flex items-center gap-3">
            <Camera className="h-5 w-5 text-cyan-300" />
            <div>
              <h2 className="text-lg font-semibold">Camera</h2>
              <p className="text-sm text-slate-300">Abra a camera e verifique foco, imagem e tremor.</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={startCameraTest} disabled={cameraState.active}>Abrir camera</Button>
            <Button type="button" variant="outline" onClick={stopCameraTest} disabled={!cameraState.active}>Encerrar camera</Button>
          </div>
          {cameraState.error ? <p className="text-sm text-amber-300">{cameraState.error}</p> : null}
          <div className="rounded-2xl overflow-hidden border border-white/10 bg-black">
            <video ref={cameraVideoRef} autoPlay playsInline muted className="w-full min-h-56 object-cover" />
          </div>
          <StatusButtons value={testStatus.camera} onChange={(value) => setTestStatus((current) => ({ ...current, camera: value }))} />
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/8 backdrop-blur-md p-5 space-y-4">
          <div>
            <h2 className="text-lg font-semibold">Botoes fisicos</h2>
            <p className="text-sm text-slate-300">Marque os botoes que responderam corretamente.</p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ["power", "Power"],
              ["volumeUp", "Volume +"],
              ["volumeDown", "Volume -"],
              ["silent", "Silent / vibracao"],
            ].map(([key, label]) => (
              <label key={key} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3">
                <input
                  type="checkbox"
                  checked={buttonChecks[key]}
                  onChange={(event) => setButtonChecks((current) => ({ ...current, [key]: event.target.checked }))}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
          <p className="text-sm text-slate-400">Sugestao automatica: {statusLabel(suggestedButtonsStatus)}</p>
          <StatusButtons value={testStatus.botoes} onChange={(value) => setTestStatus((current) => ({ ...current, botoes: value }))} />
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/8 backdrop-blur-md p-5 space-y-4">
          <div>
            <h2 className="text-lg font-semibold">Observacoes</h2>
            <p className="text-sm text-slate-300">Registre riscos, trincas, oxidacao, marcas ou qualquer detalhe importante.</p>
          </div>
          <Textarea
            value={observacoes}
            onChange={(event) => setObservacoes(event.target.value)}
            placeholder="Ex.: touch falhando no canto superior direito; aparelho com marcas na tampa."
            className="min-h-32 bg-slate-950/50 border-white/10 text-white"
          />
        </section>

        <div className="sticky bottom-4">
          <Button type="button" onClick={saveChecklist} disabled={saving} className="w-full h-12 text-base">
            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Salvar checklist
          </Button>
        </div>
      </div>
    </div>
  );
}
