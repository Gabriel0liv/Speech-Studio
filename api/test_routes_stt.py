from api.routes_stt import _build_stt_command


def test_build_stt_command_includes_initial_prompt():
    command = _build_stt_command(
        upload_path="input.wav",
        output_dir="outputs/job",
        model="medium",
        language="pt",
        device="auto",
        compute_type="int8",
        batch_size=2,
        no_diarization=False,
        num_speakers=2,
        min_speakers=None,
        max_speakers=None,
        speaker_profile=None,
        formats="txt json srt vtt",
        vad_onset=0.5,
        vad_offset=0.363,
        chunk_size=30,
        initial_prompt="Hades, Poseidon, DrathosSMP",
    )
    index = command.index("--initial-prompt")
    assert command[index + 1] == "Hades, Poseidon, DrathosSMP"


def test_build_stt_command_omits_initial_prompt_when_empty():
    command = _build_stt_command(
        upload_path="input.wav",
        output_dir="outputs/job",
        model="small",
        language=None,
        device="auto",
        compute_type="int8",
        batch_size=2,
        no_diarization=True,
        num_speakers=None,
        min_speakers=None,
        max_speakers=None,
        speaker_profile=None,
        formats="txt json srt vtt",
        vad_onset=0.5,
        vad_offset=0.363,
        chunk_size=30,
        initial_prompt=None,
    )
    assert "--initial-prompt" not in command
