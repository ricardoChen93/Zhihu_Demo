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

  var csrftoken = $('[name="csrf-token"]').attr('content');
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

  /*加载更多主页动态*/
  var feed_counter = 0;
  var feed_start = 10;
  var feed_size = 5;
  $("#zh-load-more").click(function() {
    var feed_count = parseInt($("#home-feed-list").attr("data-count"));
    var offset = feed_start + feed_counter * feed_size;
    $.ajax({
      type: "GET",
      url: "/api/HomeFeedList/",
      data: { "offset": offset, "count": feed_count },
      success: function(response) {
        $("#home-feed-list").append(response);
        if (feed_offset + feed_size >= feed_count) {
          $("#zh-load-more").hide();
        }
      }
    })
    feed_counter ++;
  });

  /*获取导航栏消息*/
  var get_notifications = function() {
    $.get("/api/notification/nav/")
      .success(function(response) {
        var count = response["not_read_count"];
        if (count != 0) { 
          $("#zh-top-nav-count").text(count);
        }
        $("#popover-noti-content").append(response["noti_html"]);
        $("#popover-noti-content").attr("data-count", response["count"]);
      });
  };
  get_notifications();

  /*发现页换一批*/
  $("#explore-random").click(function() {
    $.ajax({
      type: "GET",
      url: "/api/RandomQuestions",
      success: function(data) {
        $("a.question_link").each(function(index) {
          $(this).attr("href", data["question"][index]["link"]);
          $(this).text(data["question"][index]["title"]);
        });
      }
    })
  });

  /*导航栏消息弹窗*/
  var noti_click_counter = 1;
  var noti_counter = 0;
  var noti_start = 10;
  var noti_size = 5;
  var scrollTimer = null;
  $("#top-nav-notification")
    .popover({
      html: true,
      content: function() {
          return $('#popover-noti-content').html();
        }
    })
    .click(function() {
      if (noti_click_counter % 2 !== 0) {
        $.ajax({
          type: "POST",
          url: "/api/notification/batch/",
          success: function() {
            $("#zh-top-nav-count").empty();
          }
        })
        /*消息弹窗加载更多*/
        $(".popover-content").scroll(function() {
          if (scrollTimer) {
            clearTimeout(scrollTimer);
          }
          scrollTimer = setTimeout(loadNotis, 500);
        });

        function loadNotis() {
          scrollTimer = null;
          if ($(".popover-content").scrollTop() + $(".popover-content").innerHeight() >= $(".popover-content")[0].scrollHeight) {
            var noti_count = parseInt($("#popover-noti-content").attr("data-count"));
            var offset = noti_start + noti_counter * noti_size;
            $.ajax({
              url: "/api/NotificationList/",
              type: "GET",
              data: { "offset": offset, "count": noti_count },
              success: function(html) {
                console.log(html);
                $(".popover-content").append(html);
              }
            })
            noti_counter ++;
          }
        };
      }
      noti_click_counter += 1;
    })

});