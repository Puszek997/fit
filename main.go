package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"github.com/ebitengine/purego"
	"github.com/ebitengine/purego/objc"
	"os"
	"time"
)

type read struct {
	Rssi         int64     `json:"rssi"`
	Noise        int64     `json:"noise"`
	TransmitRate float64   `json:"transmit_rate"`
	Date         time.Time `json:"date"`
}

func main() {
	_, err := purego.Dlopen("/System/Library/Frameworks/CoreWLAN.framework/CoreWLAN", purego.RTLD_NOW|purego.RTLD_LOCAL)
	if err != nil {
		panic(err)
	}
	wifiInterface := objc.ID(objc.GetClass("CWWiFiClient")).Send(objc.RegisterName("sharedWiFiClient")).Send(objc.RegisterName("interface"))
	selRssiValue := objc.RegisterName("rssiValue")
	selNoiseMeasurement := objc.RegisterName("noiseMeasurement")
	selTransmitRate := objc.RegisterName("transmitRate")

	var numberOfReads int
	var floor int
	var turn int
	var numberOfPlaces int

	fmt.Printf("Floor: ")
	_, err = fmt.Scan(&floor)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Number of places: ")
	_, err = fmt.Scan(&numberOfPlaces)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Turn: ")
	_, err = fmt.Scan(&turn)
	if err != nil {
		panic(err)
	}

	err = os.MkdirAll(fmt.Sprintf("reads%d", turn), 0755)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Number of reads: ")
	_, err = fmt.Scan(&numberOfReads)
	if err != nil {
		panic(err)
	}

	for i := 0; i < numberOfPlaces; i++ {
		fmt.Printf("Start reading of place %d (enter \"s\" for skip) ", i+1)
		b, err := bufio.NewReader(os.Stdin).ReadBytes('\n')
		if string(b) == "s\n" {
			fmt.Println("Reading skipped")
			continue
		}
		if err != nil {
			panic(err)
		}

		reads := make([]read, 0, numberOfReads)

		for range numberOfReads {
			start := time.Now()
			reads = append(
				reads,
				read{
					Rssi:         objc.Send[int64](wifiInterface, selRssiValue),
					Noise:        objc.Send[int64](wifiInterface, selNoiseMeasurement),
					TransmitRate: objc.Send[float64](wifiInterface, selTransmitRate),
					Date:         time.Now(),
				},
			)
			time.Sleep((time.Second / 100) - time.Since(start))
		}

		jsonBytes, err := json.MarshalIndent(reads, "", "  ")
		if err != nil {
			panic(err)
		}

		err = os.WriteFile(fmt.Sprintf("reads%d/%d.%d.%d.json", turn, floor, i+1, turn), jsonBytes, 0644)
		if err != nil {
			panic(err)
		}
	}
}
