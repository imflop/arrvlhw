package main

import (
	"encoding/json"
	"fmt"
	"github.com/gorilla/websocket"
	"github.com/icrowley/fake"
	"log"
	"math/rand"

	"net/http"
	"strconv"
	"time"
)

var messagesCount int

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize:  1024,
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

func sendData(client *websocket.Conn) {
	for {
		messagesCount++
		w, err := client.NextWriter(websocket.TextMessage)
		if err != nil {
			break
		}
		random := rand.Intn(1000 - 1) + 1
		var msg []byte
		if (random > 995) {
			msg = invalid()
		} else {
			msg = newMessage()
		}
		w.Write(msg)
		w.Close()


	}
}

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		ws, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Fatal(err)
		}
		ticker := time.NewTicker(10 * time.Second)
		defer ticker.Stop()
		go sendData(ws)
		for {
			fmt.Printf("messages/second = %v \n", messagesCount / 10)
			messagesCount = 0
			<-ticker.C
		}
	})

	http.HandleFunc("/count", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(strconv.Itoa(messagesCount)))
	})

	fmt.Println("server started at :8080")
	http.ListenAndServe(":8080", nil)
}

func newMessage() []byte {
	country := fake.Country()
	random := rand.Intn(1000 - 1) + 1
	if (random > 995) {
		country = ""
	}
	data, _ := json.Marshal(map[string]string{
		"model":            fake.Model(),
		"description":      fake.Sentence(),
		"country":          country,
		"component":        fake.Product(),
	})
	return data
}

func invalid() []byte {
	return []byte("invalid json")
}