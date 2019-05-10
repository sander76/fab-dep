from pathlib import Path

HERE = Path(__file__).parent.absolute()
TEST_TEMP_FOLDER: Path = HERE.joinpath(".ease", "bin")
