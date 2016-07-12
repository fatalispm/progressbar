/**
 * Created by igormelnyk on 7/6/16.
 */
var form = document.forms.fileinfo;
var table = document.getElementById('table');
var globalData = [];
form.addEventListener('submit', function(ev) {

  var oOutput = document.querySelector("div"),
      oData = new FormData(form);

  var oReq = new XMLHttpRequest();
  oReq.open("POST", "/upload", true);
  oReq.onload = function(oEvent) {
    if (oReq.status == 200) {
        var myArr = JSON.parse(oReq.responseText);
        myArr['progress'] = 0;
        addToTable(table, myArr);
        globalData.push(myArr);
    }
  };

  oReq.send(oData);
  ev.preventDefault();
}, false);

var addToTable = function(table, data){
    var row = table.insertRow(-1);

    var name = row.insertCell(0);
    var time = row.insertCell(1);
    var status = row.insertCell(2);
    var download = row.insertCell(3);
// Add some text to the new cells:
    name.innerHTML = data['fileName'];
    time.innerHTML = data['date'];
    status.innerHTML = '0';
    download.innerHTML="Waiting ..";
};


function findInGlobalData(id){
    arr = globalData.filter(function(e){
        return e['fileId']==id;
    });
    if (arr.length>0) return arr[0];
}
function checkStatus(id){
    var xhr =new XMLHttpRequest();
    xhr.open("GET","/status/"+id, true);
    xhr.onload = function(event) {
        if (xhr.status == 200) {
            var myArr = JSON.parse(xhr.responseText);
            var e = findInGlobalData(id);
            e['progress'] = myArr['status'];
        }
    };
    xhr.send();
}

function updateProgress(table, value, row){
   table.rows[row].cells[2].innerHTML = value;
}
function setDownloadLink(table, fileName, row){
    table.rows[row].cells[3].innerHTML = "<a href = /file/"+fileName+".csv>Download</a>";
}
function updateTable(){
    updateGlobalData();
    for(var i=0;i<globalData.length;i++){
        var e = globalData[i];
        updateProgress(table, e['progress'],i+1);
        if(e['progress']=='Finished'){
            setDownloadLink(table, e['fileId'],i+1);
        }
    }
}

function updateGlobalData(){
    for(var i  = 0;i<globalData.length; i++){
        var e = globalData[i];
        if(e['progress']!='Finished'){
            checkStatus(e['fileId']);
        }
    }
}

setInterval(updateTable, 3000);