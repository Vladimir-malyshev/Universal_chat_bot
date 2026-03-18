import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Добавляем корневую директорию в path
sys.path.append(os.getcwd())

from services.audio_utils import generate_unique_filename, cleanup_files, ensure_temp_dir, TEMP_DIR

class TestAudioUtils(unittest.TestCase):
    def setUp(self):
        ensure_temp_dir()

    def test_unique_filename(self):
        fname1 = generate_unique_filename("ogg")
        fname2 = generate_unique_filename("ogg")
        self.assertNotEqual(fname1, fname2)
        self.assertTrue(fname1.endswith(".ogg"))
        self.assertIn(TEMP_DIR, fname1)

    def test_cleanup_files(self):
        # Создаем временный файл
        test_file = os.path.join(TEMP_DIR, "test_cleanup.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        self.assertTrue(os.path.exists(test_file))
        cleanup_files(test_file)
        self.assertFalse(os.path.exists(test_file))

    @patch('subprocess.run')
    def test_convert_ogg_to_wav_call(self, mock_run):
        from services.audio_utils import convert_ogg_to_wav
        mock_run.return_value = MagicMock(returncode=0)
        
        convert_ogg_to_wav("in.ogg", "out.wav")
        
        # Проверяем, что ffmpeg был вызван с правильными параметрами
        args, kwargs = mock_run.call_args
        command = args[0]
        self.assertEqual(command[0], 'ffmpeg')
        self.assertIn('-ar', command)
        self.assertIn('16000', command)
        self.assertIn('-ac', command)
        self.assertIn('1', command)

if __name__ == "__main__":
    unittest.main()
