package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"os/exec"
	"time"

	"github.com/creack/pty"
)

// volumeData -
type volumeData struct { // []volumeData
	globalY float64 // unit mm
	list    []Thick
}

// Thick -
type Thick struct {
	H float64 `json:"h"` // thickness . this is what i need to draw
}

// ./film -v=1000 -m=48
func main() {
	volumeDataSize := flag.Int("v", 0, "Volume data size")
	measureCount := flag.Int("m", 0, "measure count")
	flag.Parse()

	var base float64 = 15.0
	real_data := MakeVolumeData(*volumeDataSize, *measureCount, base)

	x, y, z := MakeTopographicData(real_data)

	saveFileName := "t.txt"
	saveDir := "./heatmap"

	if err := WriteToTmplFile(x, y, z, saveFileName); err != nil {
		fmt.Println("write to file error: ", err)
		return
	}

	fmt.Println("Start")

	scriptName := "topographic_map.py" // topographic_map
	execCommand(scriptName, saveFileName, saveDir)

	fmt.Println("Done")
}

// MakeTopographicData -
func MakeTopographicData(data []*volumeData) ([]float64, []int, [][]float64) {
	var x = []float64{}
	y := []int{}
	for i := 1; i <= len(data[0].list); i++ {
		y = append(y, i)
	}

	// var z = [][]float64{}
	z := make([][]float64, len(data[0].list))
	for _, v := range data {
		x = append(x, v.globalY)
		for i, l := range v.list {
			z[i] = append(z[i], l.H)
		}
	}

	return x, y, z
}

// WriteToTmplFile -
func WriteToTmplFile(x []float64, y []int, z [][]float64, fileName string) error {
	// 创建一个结构体来包含所有数据
	data := struct {
		X []float64   `json:"x"`
		Y []int       `json:"y"`
		Z [][]float64 `json:"z"`
	}{
		X: x,
		Y: y,
		Z: z,
	}

	file, err := os.Create(fileName)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	if err := encoder.Encode(data); err != nil {
		return err
	}

	return nil
}

func randomFloatAround15(base float64) float64 {
	rand.Seed(time.Now().UnixNano())
	return base - 0.5 + rand.Float64()
}

func FloatGenerator(start, step float64) float64 {
	current := start
	current += step
	return current
}

func MakeVolumeData(volumeDataSize, measureCount int, base float64) []*volumeData {
	rand.Seed(time.Now().UnixNano())
	var volumeDataList []*volumeData
	for i := 0; i < volumeDataSize; i++ {
		var thickList []Thick
		for j := 0; j < measureCount; j++ {
			thickList = append(thickList, Thick{
				H: randomFloatAround15(base) - base,
			})
		}

		volumeDataList = append(volumeDataList, &volumeData{
			globalY: FloatGenerator(float64(i), 1.1),
			list:    thickList,
		})
	}

	return volumeDataList
}

func execCommand(script, fileName, saveDir string) error {

	cmd := exec.Command("python3", script, fileName, saveDir)
	done := make(chan error, 1)

	f, err := pty.Start(cmd)
	if err != nil {
		done <- err
		fmt.Println("pty.Start error:", err)
	}
	defer f.Close()

	go func() {
		scanner := bufio.NewScanner(f)
		for scanner.Scan() {
			fmt.Println(scanner.Text())
		}
		done <- nil //scanner.Err()
	}()

	// Wait for the command to finish
	if err := cmd.Wait(); err != nil {
		fmt.Println(err)
	}

	return nil
}
