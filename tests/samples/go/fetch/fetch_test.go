package fetch

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestFetchDataReturnsTheBody(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		io.WriteString(w, "payload")
	}))
	defer server.Close()
	url = server.URL

	if data, ok := fetchData().(dataMsg); !ok || string(data.body) != "payload" {
		t.Fatalf("fetchData() = %#v, want dataMsg with the response body", data)
	}
}
