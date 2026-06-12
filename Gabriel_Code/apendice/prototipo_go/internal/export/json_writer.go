package export

import (
	"encoding/json"
	"os"
	"sync"
)

type JSONWriter struct {
	mu    sync.Mutex
	files map[string]*os.File
}

func NewJSONWriter() *JSONWriter {
	return &JSONWriter{
		files: make(map[string]*os.File),
	}
}

func (w *JSONWriter) Write(filename string, data interface{}) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	// Para este minerador, vamos acumular em memória e salvar no final 
	// ou fazer append em um array JSON. 
	// Para garantir performance e simplicidade, vamos escrever cada item 
	// como uma linha (JSONL) e converter para array no final se necessário,
	// ou apenas gerenciar um slice e salvar tudo no fim.
	
	// Como o objetivo é 2-4h e repositórios grandes, JSONL é mais seguro.
	f, ok := w.files[filename]
	if !ok {
		var err error
		f, err = os.OpenFile(filename, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			return err
		}
		w.files[filename] = f
	}

	b, err := json.Marshal(data)
	if err != nil {
		return err
	}

	_, err = f.Write(append(b, '\n'))
	return err
}

func (w *JSONWriter) Close() {
	w.mu.Lock()
	defer w.mu.Unlock()
	for _, f := range w.files {
		f.Close()
	}
}
