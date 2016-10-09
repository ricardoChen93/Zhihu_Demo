$(function() {
  var url = window.location.href;
  var re_topic = /topic/;
  var re_explore = /explore/;
  if (url === 'http://127.0.0.1:5000/') {
    $("#home").addClass("current");
  } else if (re_topic.test(url)) {
    $("#topic").addClass("current");
  } else if (re_explore.test(url)) {
    $("#explore").addClass("current");
  };

  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken)
      }
    }
  });
  $(".follow-button").click(function() {
    if ($(".follow-button").hasClass("btn-white")) {
      $.ajax({
        url: "/unfollow/question/" + question_id,
        data: null,
        type: "POST",
        contentType:"application/json",
        success: function() {
          $(".follow-button").text("关注问题");
          $(".follow-button").removeClass("btn-white").addClass("btn-green");
        }
      });
    } else if ($(".follow-button").hasClass("btn-green")) {
      $.ajax({
        url: "/follow/question/" + question_id,
        data: null,
        type: "POST",
        contentType:"application/json",
        success: function() {
          $(".follow-button").text("取消关注");
          $(".follow-button").removeClass("btn-green").addClass("btn-white");
        }
      });
    }
  });

  $(".answer").map(function() {
    var answer_id = $(this).attr("data-aid");
    var up_selector = ".answer[data-aid='" + answer_id + "'] .up";
    var up_count = ".answer[data-aid='" + answer_id + "'] .count";
    var up_label = ".answer[data-aid='" + answer_id + "'] .up .label";
    var down_selector = ".answer[data-aid='" + answer_id + "'] .down";
    var down_label = ".answer[data-aid='" + answer_id + "'] .down .label";
    $(up_selector).click(function() {
      var old_count = parseInt($(up_count).text());
      if ($(up_selector).hasClass("pressed")) {
        $.ajax({
          url: "/answer/" + answer_id +"/cancel_vote",
          data: null,
          type: "POST",
          contentType: "application/json",
          success: function() {
            $(up_count).text(old_count - 1);
            $(up_selector).removeClass("pressed");
            $(up_selector).attr("title", "赞同");
            $(up_label).text("赞同");
          }
        });
      } else {
        $.ajax({
          url: "/answer/" + answer_id +"/agree",
          data: null,
          type: "POST",
          contentType: "application/json",
          success: function() {
            $(up_count).text(old_count + 1);
            $(up_selector).addClass("pressed");
            $(up_selector).attr("title", "取消赞同");
            $(up_label).text("取消赞同");
            if ($(down_selector).hasClass("pressed")) {
              $(down_selector).removeClass("pressed");
              $(down_selector).attr("title", "反对，不会显示你的姓名");
              $(down_label).text("反对，不会显示你的姓名");              
            }
          }
        });
      }
    });
    $(down_selector).click(function() {
      var old_count = parseInt($(up_count).text());
      if ($(down_selector).hasClass("pressed")) {
        $.ajax({
          url: "/answer/" + answer_id +"/cancel_vote",
          data: null,
          type: "POST",
          contentType: "application/json",
          success: function() {
            $(down_selector).removeClass("pressed");
            $(down_selector).attr("title", "反对，不会显示你的姓名");
            $(down_label).text("反对，不会显示你的姓名");
          }
        });        
      } else {
        $.ajax({
          url: "/answer/" + answer_id +"/disagree",
          data: null,
          type: "POST",
          contentType: "application/json",
          success: function() {
            $(down_selector).addClass("pressed");
            $(down_selector).attr("title", "取消反对");
            $(down_label).text("取消反对");
            if ($(up_selector).hasClass("pressed")) {
              $(up_count).text(old_count - 1);
              $(up_selector).removeClass("pressed");
              $(up_selector).attr("title", "赞同");
              $(up_label).text("赞同");
            }
          }
        });        
      }
    });
  });

  $("a[name='edit']").click(function() {
    if ($.contains(document.getElementById("question-title"), this)) {
      $("#question-title .editable-content").hide();
      $("#question-title .editable-editor-wrap").show();     
    } else if ($.contains(document.getElementById("question-detail"), this)) {
      $("#question-detail .editable-content").hide();
      $("#question-detail .editable-editor-wrap").show();
    } else if ($.contains(document.getElementById("answers"), this)) {
      $(this).parent().hide();
      $(".answer .editable-editor-wrap").show();
    };
  });

  $("a[name='cancel']").click(function() {
    if ($.contains(document.getElementById("question-title"), this)) {
      $("#question-title .editable-content").show();
      $("#question-title .editable-editor-wrap").hide();
    } else if ($.contains(document.getElementById("question-detail"), this)) {
      $("#question-detail .editable-content").show();
      $("#question-detail .editable-editor-wrap").hide();
    } else if ($.contains(document.getElementById("answers"), this)) {
      $(".answer .editable-editor-wrap").prev().show();
      $(".answer .editable-editor-wrap").hide();
    };
  });

  $("a[name='save']").click(function() {
    if ($.contains(document.getElementById("question-title"), this)) {
      data = {
      "action": "edit-title",
      "reason": $("#question-title select option:selected").text(),
      "title": $("#question-title textarea").val(),
      };
      $.ajax({
        url: "/edit-question/" + question_id,
        data: JSON.stringify(data),
        type: 'POST',
        contentType: 'application/json',
        success: function() {
          location.reload();
        },
      });
    } else if ($.contains(document.getElementById("question-detail"), this)) {
      data = {
      "action": "edit-content",
      "reason": $("#question-detail select option:selected").text(),
      "content": edit_question.value(),
      };
      $.ajax({
        url: "/edit-question/" + question_id,
        data: JSON.stringify(data),
        type: 'POST',
        contentType: 'application/json',
        success: function() {
          location.reload();
        },
      });
    } else if ($.contains(document.getElementById("answers"), this)) {
      data = {"content": edit_answer.value()};
      $.ajax({
        url: "/edit-answer/" + answer_id,
        data: JSON.stringify(data),
        type: 'POST',
        contentType: 'application/json',
        success: function() {
          location.reload();
        },
      });
    };
  });

  /*首页加载更多*/
  var count = parseInt($("#home-feed-list").attr("data-count"));
  var counter = 0;
  var start = 10;
  var size = 5;
  $("#zh-load-more").click(function() {
    offset = start + counter * size;
    $.ajax({
      type: "GET",
      url: "/api/HomeFeedList/",
      data: { "offset": offset, "count": count },
      success: function(response) {
        $("#home-feed-list").append(response);
        if (offset + size >= count) {
          $("#zh-load-more").hide();
        }
      }
    })
    counter ++;
  });

});